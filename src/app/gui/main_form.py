from typing import Optional, List

from PySide2.QtGui import QIcon
from PySide2.QtWidgets import QMainWindow, QSplitter, QMessageBox

from src.app.gui.action import create_folder_action, create_open_file_action, FileAction, create_file_action, \
    create_select_folder_action, create_pin_action, create_open_folder_externally_action, \
    create_open_folder_in_new_tab_action
from src.app.gui.favorite_view import FavoriteTree
from src.app.gui.tree import TreeView
from src.app.gui.tree_box import TreeBox
from src.app.model.schema import App, CONFIG_FILE, Tree
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

    def current_tree(self) -> Optional[TreeView]:
        current_tree = self.tree_box.current_tree()
        if not current_tree:
            QMessageBox.information(self, APP_NAME, "No tab selected")
            return None
        return current_tree

    def path_func(self) -> Optional[List[str]]:
        current_tree = self.current_tree()
        return current_tree.get_selected_paths() if current_tree else None

    def init_menu(self):
        file_menu = self.menuBar().addMenu("&File")
        # Create
        self.actions[FileAction.CREATE] = create_file_action(parent=self, path_func=self.path_func)
        file_menu.addAction(self.actions[FileAction.CREATE])
        # Open
        self.actions[FileAction.OPEN] = create_open_file_action(parent=self, path_func=self.path_func)
        file_menu.addAction(self.actions[FileAction.OPEN])
        # Open file in VS code
        # folder menu
        folder_menu = self.menuBar().addMenu("Fol&der")
        # Create
        folder_menu.addAction(create_folder_action(parent=self, path_func=self.path_func))
        # Select
        folder_menu.addAction(create_select_folder_action(parent=self.current_tree()))
        # Pin
        folder_menu.addAction(create_pin_action(parent=self.current_tree(), path_func=self.path_func, pin=True))
        # Unpin
        folder_menu.addAction(create_pin_action(parent=self.current_tree(), path_func=self.path_func, pin=False))
        # Open (externally)
        folder_menu.addAction(create_open_folder_externally_action(
            parent=self.current_tree(), path_func=self.path_func
        ))
        # Open (new tab)
        folder_menu.addAction(create_open_folder_in_new_tab_action(
            parent=self.current_tree(), path_func=self.path_func
        ))

        # Open (new window)
        # Open (VS Code)
        # Open Console
        # Command menu
        # Copy
        # Paste
        # Duplicate
        # Rename
        # Delete
        # Compare
        # Selection menu
        # Copy full path
        # Copy name
        #  -----------
        # Select children/siblings
        # Invert selection
        # View menu
    #     show favorite
    # show buttons
    #

    def closeEvent(self, event):
        json_to_file(json_dict=self.app.dict(), file_name=CONFIG_FILE)
