import sys
import traceback
from typing import Optional, List

from PySide2.QtGui import QIcon, Qt
from PySide2.QtWidgets import QMainWindow, QSplitter, QMessageBox

from src.app.gui.favorite_view import FavoriteTree
from src.app.gui.menu import init_menu
from src.app.gui.tree_view import TreeView
from src.app.gui.tree_box import TreeBox
from src.app.model.schema import App, CONFIG_FILE, WindowState
from src.app.utils.constant import APP_NAME
from src.app.utils.logger import get_console_logger, get_file_handler
from src.app.utils.serializer import json_to_file

logger = get_console_logger(name=__name__)
logger.addHandler(get_file_handler())


class MainForm(QMainWindow):
    def __init__(self, app: App):
        super().__init__()
        self.process_args()
        self.app = app
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
        box = QMessageBox(QMessageBox.Critical, APP_NAME, "Unhandled exception", QMessageBox.Ok, self)
        box.setDetailedText(message)
        box.exec_()
        logger.error(message)

    def init_ui(self):
        self.setWindowTitle(self.app.name)
        self.setWindowIcon(QIcon("file_system.ico"))
        if not self.app.pages:
            self.tree_box.open_root_page()
        state: WindowState = self.app.win_state
        if state:
            self.setGeometry(state.x, state.y, state.width, state.height)
            if state.state:
                self.setWindowState(state.state)
            if state.on_top:
                self.setWindowFlags(self.windowFlags() | Qt.WindowStaysOnTopHint)
            else:
                self.setWindowFlags(self.windowFlags() & ~Qt.WindowStaysOnTopHint)
            if state.splitter_sizes:
                self.splitter.setSizes(state.splitter_sizes)
        self.splitter.splitterMoved.connect(self.on_splitter_moved)

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

    def closeEvent(self, event):
        self.app.win_state = WindowState(
            x=self.pos().x(),
            y=self.pos().y(),
            width=self.size().width(),
            height=self.size().height(),
            state=self.windowState(),
            on_top=(self.windowFlags() & ~Qt.WindowStaysOnTopHint) == Qt.WindowStaysOnTopHint,
            splitter_sizes=self.splitter.sizes(),
        )
        json_to_file(json_dict=self.app.dict(), file_name=CONFIG_FILE)
