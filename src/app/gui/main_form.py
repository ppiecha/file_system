from typing import Optional, List

from PySide2.QtGui import QIcon
from PySide2.QtWidgets import QMainWindow, QSplitter, QMessageBox

from src.app.gui.action import create_folder_action, open_file_action, FileAction, create_file_action
from src.app.gui.favorite_view import FavoriteTree
from src.app.gui.tree_box import TreeBox
from src.app.model.schema import App, CONFIG_FILE
from src.app.utils.constant import APP_NAME
from src.app.utils.serializer import json_to_file


class MainForm(QMainWindow):
    def __init__(self, app: App):
        super().__init__()
        self.app = app
        self.actions = {}
        splitter = QSplitter(self)
        self.favorite_tree = FavoriteTree(parent=splitter, favorites=app.favorites)
        self.tree_box = TreeBox(parent=splitter, app_model=app)
        splitter.addWidget(self.favorite_tree)
        splitter.addWidget(self.tree_box)
        self.setCentralWidget(splitter)
        self.init_ui()
        self.init_menu()

    def init_ui(self):
        self.setWindowTitle(self.app.name)
        self.setWindowIcon(QIcon("file_system.ico"))
        if not self.app.pages:
            self.tree_box.add_page()

    def path_func(self) -> Optional[List[str]]:
        current_tree = self.tree_box.current_tree()
        if not current_tree:
            QMessageBox.information(self, APP_NAME, "No tab selected")
            return
        return current_tree.get_selected_paths()

    def init_menu(self):
        file_menu = self.menuBar().addMenu("&File")
        # Create
        self.actions[FileAction.CREATE] = create_file_action(parent=self, path_func=self.path_func)
        file_menu.addAction(self.actions[FileAction.CREATE])
        # Open
        self.actions[FileAction.OPEN] = open_file_action(parent=self, path_func=self.path_func)
        file_menu.addAction(self.actions[FileAction.OPEN])
        # folder menu
        file_folder = self.menuBar().addMenu("Fol&der")
        # Create
        file_folder.addAction(create_folder_action(parent=self, path_func=self.path_func))
        # Pin
        # Open (externally)
        # Open (new tab)
        # Open (new window)
        # Selection menu
        # Create
        # Copy
        # Duplicate
        # Rename
        # Delete
        # ----------
        # Copy full path
        # Copy name

    def closeEvent(self, event):
        json_to_file(json_dict=self.app.dict(), file_name=CONFIG_FILE)
