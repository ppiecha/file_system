import logging
import sys
import traceback
from typing import Optional, List, Dict

from PySide2.QtGui import QIcon, Qt
from PySide2.QtWidgets import QMainWindow, QMessageBox, QApplication, QStyle, QBoxLayout, QWidget, QMenu

from src.app.gui.action.command import Action
from src.app.gui.branch_box import BranchBox, BranchPanel
from src.app.gui.dialog.base import CustomMessageBox
from src.app.gui.dialog.search.search_dlg import SearchDlg
from src.app.gui.dialog.search.search_panel import SearchWorker
from src.app.gui.favorite_view import FavoriteTree
from src.app.gui.menu import init_menu
from src.app.gui.tree_box import TreeBox
from src.app.gui.tree_view import TreeView
from src.app.model.schema import get_config_file, WindowState, App
from src.app.model.search import FileSearchResult
from src.app.utils.constant import APP_NAME, Context
from src.app.utils.logger import get_console_logger, get_file_handler
from src.app.utils.serializer import json_to_file
from src.app.utils.thread import ThreadWithWorker

logger = get_console_logger(name=__name__, log_level=logging.INFO)
logger.addHandler(get_file_handler())


class MainForm(QMainWindow):
    def __init__(self, app: App, app_qt_object: QApplication):
        super().__init__()
        self.icons = {
            "dir": self.style().standardIcon(getattr(QStyle, "SP_DirIcon")),
            "file": self.style().standardIcon(getattr(QStyle, "SP_FileIcon")),
            "warning": self.style().standardIcon(getattr(QStyle, "SP_MessageBoxWarning")),
        }

        self.process_args()
        self.app = app
        self.app_qt_object = app_qt_object
        self.actions: Dict[str, Action] = {}
        self.threads: List[ThreadWithWorker] = []
        self.group = BranchBox(parent=self, app_model=app)
        self.setCentralWidget(self.group)
        self.init_ui()
        init_menu(main_form=self)
        self.search_dlg = SearchDlg(mf=self)
        self.app_qt_object.aboutToQuit.connect(self.on_quit)

    def remove_thread(self, thread_with_worker: ThreadWithWorker):
        try:
            logger.debug(f"Removing {id(thread_with_worker)}")
            self.threads.remove(thread_with_worker)
            logger.debug(f"Threads count {len(self.threads)}")
        except ValueError:
            logger.debug("Cannot remove thread")

    def get_icon(self, res: FileSearchResult):
        if res.is_dir:
            return self.icons["dir"]
        if res.error:
            return self.icons["warning"]
        return self.icons["file"]

    def process_args(self):
        if len(sys.argv) > 1:
            opts = [opt for opt in sys.argv[1:] if opt.startswith("-")]
            # args = [arg for arg in sys.argv[1:] if not arg.startswith("-")]
            if "-w" in opts:
                sys.excepthook = self.ui_except_hook

    def ui_except_hook(self, type_, value, tb):
        message = "".join(traceback.format_exception(type_, value, tb))
        box = CustomMessageBox(
            QMessageBox.Critical,
            APP_NAME,
            f"<b>{str(value)}</b>",
            QMessageBox.Ok,
            self,
        )
        box.setInformativeText("Abnormal exception has been caught. See details below")
        box.setDetailedText(message)
        box.setDefaultButton(QMessageBox.Ok)
        box.exec_()
        logger.error(message)

    def set_geometry_and_show(self, app: QApplication):
        state: WindowState = self.app.win_state
        new_state: WindowState = self.app.win_state
        screen_rect = app.desktop().availableGeometry(self)
        if state.x < screen_rect.x():
            new_state.x = screen_rect.x()
        if state.y < screen_rect.y():
            new_state.y = screen_rect.y()
        if state.width > screen_rect.width():
            new_state.width = screen_rect.width() // 2
        if new_state.x + state.width > screen_rect.width():
            new_state.x = max(new_state.x - new_state.width, screen_rect.x())
        if state.height > screen_rect.height():
            new_state.height = screen_rect.height() // 2
        if new_state.y + state.height > screen_rect.height():
            new_state.y = max(new_state.y - new_state.height, screen_rect.y())
        logger.debug(f"available geo {screen_rect} {new_state}")
        self.resize(new_state.width, new_state.height)
        self.move(new_state.x, new_state.y)
        if state.on_top:
            self.setWindowFlags(self.windowFlags() | Qt.WindowStaysOnTopHint)
        else:
            self.setWindowFlags(self.windowFlags() & ~Qt.WindowStaysOnTopHint)
        if state.is_maximized:
            self.showMaximized()
        else:
            self.show()

    def init_ui(self):
        self.setWindowTitle(self.app.name)
        self.setWindowIcon(QIcon("file_system.ico"))

    def app_should_quit(self) -> bool:
        message = """Some <b>background threads</b> are still running<br>
                     Are you sure you want to <b>quit?</b>"""
        if len(self.threads) > 0:
            resp = QMessageBox.question(self, APP_NAME, message)
            if resp == QMessageBox.No:
                return False
            for thread in [t for t in self.threads if isinstance(t.worker, SearchWorker)]:
                thread.thread.requestInterruption()
                thread.thread.quit()
                if not thread.thread.wait():
                    logger.debug("Search thread NOT terminated")
                if [t for t in self.threads if not isinstance(t.worker, SearchWorker)]:
                    QMessageBox.information(
                        self, APP_NAME, "Shell operation in progress. " "Cancel it manually or wait to finish"
                    )
                    return False
            return True
        return True

    def closeEvent(self, event):
        if not self.app_should_quit():
            event.ignore()
            return
        self.search_dlg.close()

    def on_quit(self):
        self.save_settings()
        self.app_qt_object.deleteLater()

    def save_settings(self):
        if not self.isMaximized():
            self.app.win_state.x = self.frameGeometry().x()
            self.app.win_state.y = self.frameGeometry().y()
            self.app.win_state.width = self.size().width()
            self.app.win_state.height = self.size().height()
        self.app.win_state.is_maximized = self.isMaximized()
        self.app.win_state.on_top = (self.windowFlags() & ~Qt.WindowStaysOnTopHint) == Qt.WindowStaysOnTopHint
        # self.app.win_state.splitter_sizes = self.splitter.sizes()
        self.group.store_branches_layout()
        self.group.save_pinned_paths()
        self.app.last_branch = self.group.current_branch_panel().branch.name
        json_to_file(json_dict=self.app.dict(), file_name=get_config_file())

    def current_branch_panel(self) -> Optional[BranchPanel]:
        return self.group.current_branch_panel()

    def current_favorite_tree(self) -> Optional[FavoriteTree]:
        current_branch = self.current_branch_panel()
        if not current_branch:
            QMessageBox.information(self, APP_NAME, "No group selected")
            return None
        return current_branch.favorite_tree

    def current_tree(self) -> Optional[TreeView]:
        current_branch = self.current_branch_panel()
        if not current_branch:
            QMessageBox.information(self, APP_NAME, "No group selected")
            return None
        current_tree = current_branch.tree_box.current_tree()
        if not current_tree:
            QMessageBox.information(self, APP_NAME, "No tab selected")
            return None
        return current_tree

    def current_tree_box(self) -> TreeBox:
        return self.current_tree().tree_box

    def path_func(self) -> Optional[List[str]]:
        if self.isActiveWindow():
            if (current_tree := self.current_tree()).hasFocus():
                if not current_tree:
                    return []
                paths = current_tree.get_selected_paths()
                if len(paths) > 0:
                    return paths
            if (current_tree := self.current_favorite_tree()).hasFocus():
                return [current_tree.current_favorite().path]
        if self.search_dlg.isActiveWindow() and self.search_dlg.search_control.currentWidget():
            paths = self.search_dlg.search_control.currentWidget().search_tree.get_selected_paths()
            if len(paths) > 0:
                return paths
        QMessageBox.information(self, APP_NAME, "No path selected")
        return []

    def context_func(self) -> Context:
        if self.isActiveWindow():
            return Context.main
        if self.search_dlg.isActiveWindow():
            return Context.search
        raise ValueError("Undefined context")

    def line_func(self):
        if self.search_dlg.isActiveWindow() and self.search_dlg.search_control.currentWidget():
            return self.search_dlg.search_control.currentWidget().search_tree.get_paths_with_hits()
        return []

    def activate(self):
        self.activateWindow()
        self.show()
