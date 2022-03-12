import sys
from enum import Enum
from typing import List

from PySide2.QtCore import QDir, QFileInfo, QModelIndex, QPoint
from PySide2.QtGui import Qt
from PySide2.QtWidgets import QTreeView, QFileSystemModel, QApplication, QMenu, QAbstractItemView, QInputDialog

from src.app.gui.action import create_folder_action, create_file_action, create_pin_action, open_console_action, \
    open_folder_action, open_file_action
from src.app.gui.palette import dark_palette
from src.app.model.path import all_folders, all_files, is_single, parent_path
from src.app.model.schema import Tree
from src.app.utils.logger import get_console_logger
from src.app.utils.shell import start_file

logger = get_console_logger(name=__name__)


class TreeColumn(int, Enum):
    SIZE = 1
    TYPE = 2
    DATE = 3


class TreeView(QTreeView):
    def __init__(self, parent, tree: Tree):
        super().__init__(parent)
        self.setModel(QFileSystemModel())
        self.model().setRootPath(tree.root_path)
        self.init_ui(tree=tree)

    @property
    def root_path(self) -> str:
        return self.model().rootPath()

    @root_path.setter
    def root_path(self, path: str):
        self.model().setRootPath(path)
        # self.setRootIndex(self.model().index(path))
        logger.debug(f"root path {path}")

    def pin(self, path: str, pin: bool):
        if pin:
            self.setRootIndex(self.model().index(path))
        else:
            self.setRootIndex(QModelIndex())

    @property
    def current_path(self) -> str:
        return self.model().fileInfo(self.currentIndex()).absoluteFilePath()

    @current_path.setter
    def current_path(self, path: str):
        if path:
            index = self.model().index(path)
            self.setCurrentIndex(index)
            self.scrollTo(index, QAbstractItemView.ScrollHint.PositionAtCenter)
        logger.debug(f"current path {path}")

    @property
    def filter(self) -> QDir.Filters:
        return self.model().filter

    @filter.setter
    def filter(self, filters: QDir.Filters):
        self.model().setFilter(filters)

    @staticmethod
    def get_filter(files: bool = True, hidden: bool = False, system: bool = False) -> QDir.Filters:
        f = QDir.Drives | QDir.Dirs | QDir.NoDotAndDotDot
        if files:
            f = f | QDir.Files
        if hidden:
            f = f | QDir.Hidden
        if system:
            f = f | QDir.System
        return f

    def hide_column(self, column: TreeColumn, hide: bool = True):
        self.setColumnHidden(column, hide)

    def hide_header(self, hide: bool = True):
        self.header().setHidden(hide)

    def init_ui(self, tree: Tree):
        self.hide_header(hide=tree.hide_header)
        for column in TreeColumn:
            self.hide_column(column=column.value, hide=column.value not in tree.visible_columns)
        self.root_path = tree.root_path
        self.current_path = tree.current_path
        self.filter = TreeView.get_filter()
        self.setAcceptDrops(True)
        self.setDragEnabled(True)
        self.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.setContextMenuPolicy(Qt.CustomContextMenu)

        self.clicked.connect(self.on_clicked)
        self.doubleClicked.connect(self.on_double_clicked)
        self.customContextMenuRequested.connect(self.open_menu)

    def get_selected_paths(self) -> List[str]:
        return [self.model().fileInfo(index).absoluteFilePath()
                for index in self.selectedIndexes()]

    def on_clicked(self, index):
        path = self.model().fileInfo(index).absoluteFilePath()
        logger.debug(f"Tree selected path {path}")

    def on_double_clicked(self, index):
        path = QFileInfo(self.model().fileInfo(index).absoluteFilePath())
        if path.isFile():
            start_file(file_name=path.absoluteFilePath())

    def open_menu(self, position):
        paths = self.get_selected_paths()
        if paths is not None and len(paths) > 0:
            menu = QMenu()
            if all_folders(paths=paths):
                if is_single(paths=paths):
                    menu.addAction(create_folder_action(parent=self, path=paths[0]))
                    menu.addAction(create_file_action(parent=self, path=paths[0]))
                    menu.addSeparator()
                    menu.addAction(create_pin_action(parent=self, path=paths[0], pin=True))
                    menu.addAction(create_pin_action(parent=self, path=paths[0], pin=False))
                    menu.addSeparator()
                    menu.addAction(open_console_action(parent=self, path=paths[0]))
                menu.addAction(open_folder_action(parent=self, paths=paths))
            elif all_files(paths=paths):
                menu.addAction(create_file_action(parent=self, path=paths[0]))
                menu.addAction(open_file_action(parent=self, paths=paths))
            else:
                pass
            menu.exec_(self.viewport().mapToGlobal(position))

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.accept()
        else:
            event.ignore()

    def dragMoveEvent(self, event):
        # print(type(event))
        # event.accept()
        index = self.indexAt(event.pos())
        path = self.model().fileInfo(index).absoluteFilePath()
        logger.debug(path)
        if event.mimeData().hasUrls:
            event.setDropAction(Qt.CopyAction)
            event.accept()
        else:
            event.ignore()

    def dropEvent(self, event):
        files = [u.toLocalFile() for u in event.mimeData().urls()]
        for f in files:
            print(f)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setStyle('Fusion')  # Style needed for palette to work
    app.setPalette(dark_palette)
    tree = TreeView(parent=None, tree=Tree(root_path="c:\\", current_path="c:\\Users\\piotr\\temp"))
    tree.show()
    tree.current_path = tree.current_path
    sys.exit(app.exec_())

