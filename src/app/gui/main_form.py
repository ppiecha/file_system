import sys
import traceback
from typing import Optional, List

from PySide2.QtGui import QIcon, Qt
from PySide2.QtWidgets import QMainWindow, QSplitter, QMessageBox, QApplication

from src.app.gui.dialog.base import CustomMessageBox
from src.app.gui.favorite_view import FavoriteTree
from src.app.gui.menu import init_menu
from src.app.gui.tree_view import TreeView
from src.app.gui.tree_box import TreeBox
from src.app.model.schema import App, get_config_file, WindowState
from src.app.utils.constant import APP_NAME
from src.app.utils.logger import get_console_logger, get_file_handler
from src.app.utils.serializer import json_to_file

logger = get_console_logger(name=__name__)
logger.addHandler(get_file_handler())


class MainForm(QMainWindow):
    def __init__(self, app: App, app_qt_object: QApplication):
        super().__init__()
        self.process_args()
        self.app = app
        self.app_qt_object = app_qt_object
        self.actions = {}
        self.threads = []
        self.splitter = QSplitter(self)
        self.favorite_tree = FavoriteTree(parent=self.splitter, app_model=app)
        self.tree_box = TreeBox(parent=self.splitter, app_model=app)
        self.splitter.addWidget(self.favorite_tree)
        self.splitter.addWidget(self.tree_box)
        self.setCentralWidget(self.splitter)
        self.init_ui()
        init_menu(main_form=self)

    def process_args(self):
        if len(sys.argv) > 1:
            opts = [opt for opt in sys.argv[1:] if opt.startswith("-")]
            # args = [arg for arg in sys.argv[1:] if not arg.startswith("-")]
            if "-w" in opts:
                sys.excepthook = self.except_hook
        else:
            pass

    def except_hook(self, type_, value, tb):
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
        if not self.app.pages:
            self.tree_box.open_root_page()
        if self.app.win_state and self.app.win_state.splitter_sizes:
            self.splitter.setSizes(self.app.win_state.splitter_sizes)
        self.splitter.splitterMoved.connect(self.on_splitter_moved)

    def save_settings(self):
        json_to_file(json_dict=self.app.dict(), file_name=get_config_file())

    def closeEvent(self, event):
        if not self.isMaximized():
            self.app.win_state.x = self.frameGeometry().x()
            self.app.win_state.y = self.frameGeometry().y()
            self.app.win_state.width = self.size().width()
            self.app.win_state.height = self.size().height()
        self.app.win_state.is_maximized = self.isMaximized()
        self.app.win_state.on_top = (self.windowFlags() & ~Qt.WindowStaysOnTopHint) == Qt.WindowStaysOnTopHint
        self.app.win_state.splitter_sizes = self.splitter.sizes()
        self.tree_box.store_pages_layout()
        if current_tree := self.tree_box.current_tree():
            self.app.last_page_pinned_path = current_tree.pinned_path
        json_to_file(json_dict=self.app.dict(), file_name=get_config_file())

    def on_splitter_moved(self, pos, index):
        self.app.win_state.splitter_sizes = self.splitter.sizes()

    def current_tree(self) -> Optional[TreeView]:
        current_tree = self.tree_box.current_tree()
        if not current_tree:
            QMessageBox.information(self, APP_NAME, "No tab selected")
            return None
        return current_tree

    def path_func(self) -> Optional[List[str]]:
        current_tree = self.current_tree()
        if not current_tree:
            return []
        paths = current_tree.get_selected_paths()
        if len(paths) > 0:
            # return [path for path in paths if QFileInfo(path).exists()]
            return paths
        QMessageBox.information(self, APP_NAME, "No path selected")
        return []
