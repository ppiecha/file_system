import os
from enum import Enum
from typing import List, Optional, Callable, Set

from PySide2.QtCore import QDir, QFileInfo, QModelIndex, QSortFilterProxyModel
from PySide2.QtGui import Qt, QPainter
from PySide2.QtWidgets import (
    QTreeView,
    QFileSystemModel,
    QMenu,
    QAbstractItemView,
    QFileDialog,
    QApplication, QStyleOptionViewItem,
)

from src.app.gui.action.common import CommonAction
from src.app.gui.action.file import FileAction
from src.app.gui.action.folder import FolderAction
from src.app.utils import path_util
from src.app.utils.path_util import path_caption
from src.app.model.schema import Tree
from src.app.utils.constant import APP_NAME
from src.app.utils.logger import get_console_logger
from src.app.utils.shell import start_file, open_folder

logger = get_console_logger(name=__name__)


class TreeColumn(int, Enum):
    SIZE = 1
    TYPE = 2
    DATE = 3


class TreeView(QTreeView):
    def __init__(self, parent, tree_model: Tree, selection: List[str] = None):
        super().__init__(parent)
        self.tree_box = parent
        self.main_form = self.tree_box.parent().parent()
        self.sys_model = QFileSystemModel()
        self.proxy = SortFilterModel(self)
        self.proxy.setSourceModel(self.sys_model)
        self.proxy.setDynamicSortFilter(True)
        self.setModel(self.proxy)
        self.setSortingEnabled(True)
        self.header().setSortIndicator(0, Qt.AscendingOrder)
        self.loaded_paths: Set[str] = set()
        self.tree_model = tree_model
        self.filtered_indexes = []
        self.init_ui()
        if selection:
            if len(selection) == 1:
                self.current_path = selection[0]
            else:
                raise RuntimeError("Only one selection supported")

    def init_ui(self):
        self.hide_header(hide=self.tree_model.hide_header)
        for column in TreeColumn:
            self.hide_column(column=column.value, hide=column.value not in self.tree_model.visible_columns)
        self.sys_model.directoryLoaded.connect(self.on_dir_loaded)
        self.sys_model.setRootPath(None)
        self.pinned_path = self.tree_model.pinned_path
        if self.tree_model.current_path:
            self.current_path = self.tree_model.current_path
        self.filter = TreeView.get_filter()
        self.setAcceptDrops(True)
        self.setDragEnabled(True)
        self.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.setContextMenuPolicy(Qt.CustomContextMenu)

        self.clicked.connect(self.on_clicked)
        self.activated.connect(self.on_activated)
        self.customContextMenuRequested.connect(self.open_menu)

    def drawRow(self, painter: QPainter, options: QStyleOptionViewItem, index: QModelIndex) -> None:

        super().drawRow(painter, options, index)

    def proxy_index(self, sys_index: QModelIndex) -> QModelIndex:
        if not sys_index.isValid():
            raise ValueError(f"Sys index is not valid {sys_index}")
        index = self.proxy.mapFromSource(sys_index)
        if not index.isValid():
            raise ValueError(f"Mapped index is not valid {index}")
        return index

    def sys_index(self, proxy_index: QModelIndex) -> QModelIndex:
        if not proxy_index.isValid():
            raise ValueError(f"Proxy index is not valid {proxy_index}")
        index = self.proxy.mapToSource(proxy_index)
        if not index.isValid():
            raise ValueError(f"Mapped index is not valid {index}")
        return index

    def on_dir_loaded(self, path: str):
        logger.debug(f"Path {path} loaded")
        self.loaded_paths.add(path)
        if path == self.tree_model.pinned_path:
            self.pinned_path = path

    @property
    def current_path(self) -> Optional[str]:
        if self.currentIndex().isValid():
            return self.sys_model.fileInfo(self.sys_index(proxy_index=self.currentIndex())).absoluteFilePath()
        return None

    @current_path.setter
    def current_path(self, path: str):
        if path:
            index = self.proxy_index(sys_index=self.sys_model.index(path))
            self.setCurrentIndex(index)
            self.scrollTo(index, QAbstractItemView.ScrollHint.PositionAtCenter)
        self.tree_model.current_path = path

    @property
    def pinned_path(self) -> Optional[str]:
        return self.tree_model.pinned_path

    @pinned_path.setter
    def pinned_path(self, path: str):
        parent_path = path_util.parent_path(path=path)
        if parent_path not in self.loaded_paths:
            self.sys_model.setRootPath(parent_path)
        if path not in self.loaded_paths:
            self.sys_model.setRootPath(path)
        self.tree_model.pinned_path = path
        self.tree_box.setTabText(self.tree_box.indexOf(self), path_caption(path=path))
        self._pin(path=path, pin=path is not None)

    def select_folder(self):
        path = QFileDialog.getExistingDirectory(self, APP_NAME, self.current_path)
        if path:
            self.pinned_path = path

    def pin(self, path_func: Callable, pin: bool):
        is_ok, path = path_util.validate_single_path(parent=self, paths=path_func())
        if is_ok and path:
            self.pinned_path = path if pin else None

    def _pin(self, path: str, pin: bool) -> bool:
        def show_children(path: QModelIndex):
            ind = self.proxy_index(sys_index=self.sys_model.index(path))
            # sys_ind = self.sys_index(proxy_index=ind)
            # sys_path = self.sys_model.filePath(sys_ind)
            logger.debug(f"showing children under {path}")
            logger.debug(f"rows to show {range(self.proxy.rowCount(ind))}")
            for row in range(self.proxy.rowCount(ind)):
                row_index = self.proxy.index(row, 0, ind)
                sys_index = self.sys_index(proxy_index=row_index)
                file_path = self.sys_model.filePath(sys_index)
                logger.debug(f"show child {file_path}")
                self.setRowHidden(row, ind, False)

        if pin:
            if path in self.loaded_paths:
                parent_path = path_util.parent_path(path)
                logger.debug(f"pinned parent path {parent_path} path {path}")
                if path != parent_path:
                    parent_index = self.proxy_index(sys_index=self.sys_model.index(parent_path))
                    logger.debug(f"parent index {parent_index}")
                    self.setRootIndex(parent_index)
                    self.filtered_indexes.append(parent_path)
                    logger.debug(
                        f"children of {self.sys_model.filePath(self.sys_index(proxy_index=parent_index))} "
                        f"valid {parent_index.isValid()} "
                        f"{list(range(self.proxy.rowCount(parent_index)))}"
                    )
                    for row in range(self.proxy.rowCount(parent_index)):
                        row_index = self.proxy.index(row, 0, parent_index)
                        sys_index = self.sys_index(proxy_index=row_index)
                        file_path = self.sys_model.filePath(sys_index)
                        self.setRowHidden(row, parent_index, file_path != path)
                        if file_path == path:
                            self.expand(row_index)
                        logger.debug(f"hiding row {file_path}")
            else:
                logger.debug(f"path {path} NOT LOADED YET")
                return False
        else:
            self.setRootIndex(QModelIndex())
            for index in self.filtered_indexes:
                show_children(path=index)
            self.filtered_indexes.clear()
        return True

    @property
    def filter(self) -> QDir.Filters:
        return self.sys_model.filter()

    @filter.setter
    def filter(self, filters: QDir.Filters):
        self.sys_model.setFilter(filters)

    @staticmethod
    def get_filter(files: bool = True, hidden: bool = False, system: bool = False) -> QDir.Filters:
        f = QDir.Drives | QDir.Dirs | QDir.NoDotAndDotDot | QDir.DirsFirst
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
        return [
            self.sys_model.fileInfo(self.proxy.mapToSource(index)).absoluteFilePath()
            for index in self.selectedIndexes()
        ]

    def on_clicked(self, index):
        path = self.sys_model.fileInfo(self.proxy.mapToSource(index)).absoluteFilePath()
        logger.debug(f"Tree selected path {path}")

    def open_menu(self, position):
        paths = self.get_selected_paths()
        if paths is not None and len(paths) > 0:
            menu = QMenu()
            if path_util.all_folders(paths=paths):
                if path_util.is_single(paths=paths):
                    menu.addAction(self.main_form.actions[FolderAction.CREATE])
                    menu.addAction(self.main_form.actions[FileAction.CREATE])
                    menu.addSeparator()
                    menu.addAction(self.main_form.actions[FolderAction.PIN])
                    menu.addAction(self.main_form.actions[FolderAction.UNPIN])
                    menu.addSeparator()
                    menu.addAction(self.main_form.actions[CommonAction.RENAME])
                    menu.addAction(self.main_form.actions[CommonAction.DUPLICATE])
                menu.addAction(self.main_form.actions[FolderAction.OPEN_EXT])
                menu.addAction(self.main_form.actions[FolderAction.OPEN_TAB])
                menu.addAction(self.main_form.actions[FolderAction.OPEN_CONSOLE])
            elif path_util.all_files(paths=paths):
                menu.addAction(self.main_form.actions[FileAction.CREATE])
                menu.addAction(self.main_form.actions[FileAction.OPEN])
            menu.addSeparator()
            menu.addAction(self.main_form.actions[CommonAction.RENAME])
            menu.addAction(self.main_form.actions[CommonAction.DUPLICATE])
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
        path = self.sys_model.fileInfo(self.proxy.mapToSource(index)).absoluteFilePath()
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

    def on_activated(self, index: QModelIndex):
        item_path = self.sys_model.fileInfo(self.proxy.mapToSource(index)).absoluteFilePath()
        logger.debug(f"activated item path {item_path}")
        path = QFileInfo(item_path)
        if path.isFile():
            start_file(file_name=path.absoluteFilePath())
            return
        if path.isDir():
            modifiers = QApplication.keyboardModifiers()
            if modifiers == Qt.ControlModifier:
                open_folder(dir_name=item_path)
            else:
                ind = self.proxy_index(sys_index=self.sys_model.index(item_path))
                logger.debug(f"activated proxy index valid {ind.isValid()} children {self.proxy.rowCount(ind)}")
                # if self.proxy.rowCount(ind) > 0:
                if self.isExpanded(index):
                    self.collapse(index)
                else:
                    self.expand(index)


class SortFilterModel(QSortFilterProxyModel):
    def lessThan(self, left, right):
        left_path = self.sourceModel().filePath(left)
        right_path = self.sourceModel().filePath(right)
        return (not os.path.isdir(left_path), left_path.lower()) < (not os.path.isdir(right_path), right_path.lower())
