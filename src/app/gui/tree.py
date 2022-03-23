import sys
from enum import Enum
from time import sleep
from typing import List, Optional, Callable, Dict, Set

from PySide2.QtCore import QDir, QFileInfo, QModelIndex, QPoint
from PySide2.QtGui import Qt
from PySide2.QtWidgets import QTreeView, QFileSystemModel, QApplication, QMenu, QAbstractItemView, QInputDialog, \
    QFileDialog

from src.app.gui.action import (
    create_folder_action,
    create_file_action,
    create_pin_action,
    create_open_console_action,
    create_open_folder_externally_action,
    create_open_file_action,
)
from src.app.gui.palette import dark_palette
from src.app.model.path import all_folders, all_files, is_single, parent_path, validate_single_path
from src.app.model.schema import Tree
from src.app.utils.constant import APP_NAME
from src.app.utils.logger import get_console_logger
from src.app.utils.shell import start_file

logger = get_console_logger(name=__name__)


class TreeColumn(int, Enum):
    SIZE = 1
    TYPE = 2
    DATE = 3


class TreeView(QTreeView):
    def __init__(self, parent, tree_model: Tree):
        super().__init__(parent)
        self.tree_box = parent
        self.setModel(QFileSystemModel())
        self.loaded_paths: Set[str] = set()
        self.tree_model = tree_model
        self.filtered_indexes = []
        self.init_ui()

    def init_ui(self):
        self.hide_header(hide=self.tree_model.hide_header)
        for column in TreeColumn:
            self.hide_column(column=column.value, hide=column.value not in self.tree_model.visible_columns)
        self.model().directoryLoaded.connect(self.on_dir_loaded)
        self.root_path = parent_path(path=self.tree_model.pinned_path)
        self.root_path = self.tree_model.pinned_path
        self.current_path = self.tree_model.current_path
        self.pinned_path = self.tree_model.pinned_path
        self.filter = TreeView.get_filter()
        self.setAcceptDrops(True)
        self.setDragEnabled(True)
        self.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.setContextMenuPolicy(Qt.CustomContextMenu)

        self.clicked.connect(self.on_clicked)
        self.doubleClicked.connect(self.on_double_clicked)
        self.customContextMenuRequested.connect(self.open_menu)

    def on_dir_loaded(self, path: str):
        logger.debug(f"Path {path} loaded")
        self.loaded_paths.add(path)
        if path == self.tree_model.pinned_path:
            self.pinned_path = path

    @property
    def current_path(self) -> str:
        return self.model().fileInfo(self.currentIndex()).absoluteFilePath()

    @current_path.setter
    def current_path(self, path: str):
        if path:
            index = self.model().index(path)
            self.setCurrentIndex(index)
            self.scrollTo(index, QAbstractItemView.ScrollHint.PositionAtCenter)
        self.tree_model.current_path = path

    @property
    def root_path(self) -> str:
        return self.model().rootPath()

    @root_path.setter
    def root_path(self, path: str):
        self.model().setRootPath(path)
        # self.setRootIndex(self.model().index(path))
        self.tree_model.root_path = path
        logger.debug(f"tree root path set to {path}")

    @property
    def pinned_path(self) -> Optional[str]:
        return self.tree_model.pinned_path

    @pinned_path.setter
    def pinned_path(self, path: str):
        self._pin(path=path, pin=path is not None)
        self.tree_model.pinned_path = path

    def select_folder(self):
        path = QFileDialog.getExistingDirectory(self, APP_NAME, self.current_path)
        if path:
            self.pinned_path = path

    def pin(self, path_func: Callable, pin: bool):
        is_ok, path = validate_single_path(parent=self, paths=path_func())
        if is_ok and path:
            self.pinned_path = path if pin else None

    def _pin(self, path: str, pin: bool):
        def show_children(index: QModelIndex):
            for row in range(self.model().rowCount(index)):
                self.setRowHidden(row, index, False)

        if pin:
            if path in self.loaded_paths:
                parent_path_val = parent_path(path)
                logger.debug(f"pinned parent path {parent_path_val} path {path}")
                if path != parent_path_val:
                    parent_index = self.model().index(parent_path_val)
                    self.setRootIndex(parent_index)
                    self.filtered_indexes.append(parent_index)
                    logger.debug(f"children of {self.model().filePath(parent_index)} valid {parent_index.isValid()} "
                                 f"{list(range(self.model().rowCount(parent_index)))}")
                    for row in range(self.model().rowCount(parent_index)):
                        row_index = self.model().index(row, 0, parent_index)
                        self.setRowHidden(row, parent_index, self.model().filePath(row_index) != path)
                        if self.model().filePath(row_index) == path:
                            self.expand(row_index)
                        logger.debug(f"hiding row {self.model().filePath(row_index)}")
            else:
                logger.debug(f"path {path} not loaded yet")
        else:
            for index in self.filtered_indexes:
                show_children(index=index)
            self.filtered_indexes.clear()
            self.setRootIndex(QModelIndex())

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

    def get_selected_paths(self) -> List[str]:
        return [self.model().fileInfo(index).absoluteFilePath() for index in self.selectedIndexes()]

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
                    menu.addAction(create_folder_action(parent=self, path_func=self.get_selected_paths))
                    menu.addAction(create_file_action(parent=self, path=paths[0]))
                    menu.addSeparator()
                    menu.addAction(create_pin_action(parent=self, path=paths[0], pin=True))
                    menu.addAction(create_pin_action(parent=self, path=paths[0], pin=False))
                    menu.addSeparator()
                    menu.addAction(create_open_console_action(parent=self, path=paths[0]))
                menu.addAction(create_open_folder_externally_action(parent=self, paths=paths))
            elif all_files(paths=paths):
                menu.addAction(create_file_action(parent=self, path=paths[0]))
                menu.addAction(create_open_file_action(parent=self, paths=paths))
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
            logger.debug(f"dropped file {f}")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")  # Style needed for palette to work
    app.setPalette(dark_palette)
    # tree = TreeView(parent=None, tree_model=Tree(root_path="c:\\", current_path="c:\\Users\\piotr\\temp"))
    tree = TreeView(parent=None, tree_model=Tree())
    tree.show()
    tree.current_path = tree.current_path
    sys.exit(app.exec_())
