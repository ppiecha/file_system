from PySide2.QtGui import QIcon
from PySide2.QtWidgets import QMainWindow, QSplitter

from src.app.gui.favorite_view import FavoriteTree
from src.app.gui.tree_box import TreeBox
from src.app.model.schema import App, CONFIG_FILE
from src.app.utils.serializer import json_to_file


class MainForm(QMainWindow):
    def __init__(self, app: App):
        super().__init__()
        self.app = app
        splitter = QSplitter(self)
        self.favorite_tree = FavoriteTree(parent=splitter, favorites=app.favorites)
        self.tree_box = TreeBox(parent=splitter, app_model=app)
        splitter.addWidget(self.favorite_tree)
        splitter.addWidget(self.tree_box)
        self.setCentralWidget(splitter)
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle(self.app.name)
        self.setWindowIcon(QIcon("file_system.ico"))
        if not self.app.pages:
            self.tree_box.add_page()

    def closeEvent(self, event):
        json_to_file(json_dict=self.app.dict(), file_name=CONFIG_FILE)
