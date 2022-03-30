from typing import Optional, List

from PySide2.QtGui import QIcon, Qt
from PySide2.QtWidgets import QMainWindow, QSplitter, QMessageBox

from src.app.gui.action import (
    create_folder_action,
    create_open_file_action,
    FileAction,
    create_file_action,
    create_select_folder_action,
    create_pin_action,
    create_open_folder_externally_action,
    create_open_folder_in_new_tab_action,
    FolderAction,
    create_open_console_action,
    TabAction,
    create_new_tab_action,
    create_close_tab_action,
    create_file_from_clipboard_text_action,
)
from src.app.gui.favorite_view import FavoriteTree
from src.app.gui.tree_view import TreeView
from src.app.gui.tree_box import TreeBox
from src.app.model.schema import App, CONFIG_FILE, WindowState
from src.app.utils.constant import APP_NAME
from src.app.utils.serializer import json_to_file


class MainForm(QMainWindow):
    def __init__(self, app: App):
        super().__init__()
        self.app = app
        self.actions = {}
        self.splitter = QSplitter(self)
        self.favorite_tree = FavoriteTree(parent=self.splitter, app_model=app)
        self.tree_box = TreeBox(parent=self.splitter, app_model=app)
        self.splitter.addWidget(self.favorite_tree)
        self.splitter.addWidget(self.tree_box)
        self.setCentralWidget(self.splitter)
        self.init_ui()
        self.init_menu()

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
        return current_tree.get_selected_paths() if current_tree else None

    def init_menu(self):
        file_menu = self.menuBar().addMenu("&File")
        # Create
        self.actions[FileAction.CREATE] = create_file_action(parent=self, path_func=self.path_func)
        file_menu.addAction(self.actions[FileAction.CREATE])
        # Open
        self.actions[FileAction.OPEN] = create_open_file_action(parent_func=self.current_tree, path_func=self.path_func)
        file_menu.addAction(self.actions[FileAction.OPEN])
        # Create from clipboard text
        self.actions[FileAction.CREATE_CLIP] = create_file_from_clipboard_text_action(
            parent=self, path_func=self.path_func
        )
        file_menu.addAction(self.actions[FileAction.CREATE_CLIP])
        # Open file in VS code
        # folder menu
        folder_menu = self.menuBar().addMenu("Fol&der")
        # Create
        self.actions[FolderAction.CREATE] = create_folder_action(parent=self, path_func=self.path_func)
        folder_menu.addAction(self.actions[FolderAction.CREATE])
        # Select
        self.actions[FolderAction.SELECT] = create_select_folder_action(parent_func=self.current_tree)
        folder_menu.addAction(self.actions[FolderAction.SELECT])
        # Pin
        self.actions[FolderAction.PIN] = create_pin_action(
            parent_func=self.current_tree, path_func=self.path_func, pin=True
        )
        folder_menu.addAction(self.actions[FolderAction.PIN])
        # Unpin
        self.actions[FolderAction.UNPIN] = create_pin_action(
            parent_func=self.current_tree, path_func=self.path_func, pin=False
        )
        folder_menu.addAction(self.actions[FolderAction.UNPIN])
        # Open (externally)
        self.actions[FolderAction.OPEN_EXT] = create_open_folder_externally_action(
            parent_func=self.current_tree, path_func=self.path_func
        )
        folder_menu.addAction(self.actions[FolderAction.OPEN_EXT])
        # Open (new tab)
        self.actions[FolderAction.OPEN_TAB] = create_open_folder_in_new_tab_action(
            parent_func=self.current_tree, path_func=self.path_func
        )
        folder_menu.addAction(self.actions[FolderAction.OPEN_TAB])

        # Open (new window)
        # Open (VS Code)
        # Open Console
        self.actions[FolderAction.OPEN_CONSOLE] = create_open_console_action(
            parent_func=self.current_tree, path_func=self.path_func
        )
        folder_menu.addAction(self.actions[FolderAction.OPEN_CONSOLE])
        # Command menu
        command_menu = self.menuBar().addMenu("&Command")
        # Copy
        # Paste
        # Duplicate
        # Rename
        # Delete
        # Compare
        # Selection menu
        selection_menu = self.menuBar().addMenu("&Selection")
        # Copy full path
        # Copy name
        #  -----------
        # Select children/siblings
        # Invert selection
        # Tab menu
        tab_menu = self.menuBar().addMenu("&Tab")
        self.actions[TabAction.NEW] = create_new_tab_action(parent=self.tree_box)
        tab_menu.addAction(self.actions[TabAction.NEW])
        self.actions[TabAction.CLOSE] = create_close_tab_action(
            parent_func=lambda: self.tree_box, index_func=self.tree_box.currentIndex
        )
        tab_menu.addAction(self.actions[TabAction.CLOSE])
        # View menu
        view_menu = self.menuBar().addMenu("&View")
        # show favorite
        # show buttons
        # file filter
        # always on top

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
