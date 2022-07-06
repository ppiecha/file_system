import os
import logging
from enum import Enum
from typing import List, Optional, Callable, Set, Any

from PySide2.QtCore import QDir, QFileInfo, QModelIndex, QSortFilterProxyModel, QItemSelection
from PySide2.QtGui import Qt, QPainter, QPalette, QDropEvent, QDragMoveEvent, QDragEnterEvent
from PySide2.QtWidgets import (
    QTreeView,
    QFileSystemModel,
    QMenu,
    QAbstractItemView,
    QFileDialog,
    QApplication,
    QStyleOptionViewItem,
)

from src.app.gui.action.command import CommonAction
from src.app.gui.action.file import FileAction
from src.app.gui.action.folder import FolderAction
from src.app.utils import path_util
from src.app.utils.path_util import path_caption, convert_size, file_first_lines, dir_list
from src.app.model.schema import Tree
from src.app.utils.constant import APP_NAME
from src.app.utils.logger import get_console_logger
from src.app.utils.shell import start_file, open_folder, copy, move
from src.app.utils.thread import run_in_thread

logger = get_console_logger(name=__name__, log_level=logging.INFO)


class TreeColumn(int, Enum):
    SIZE = 1
    TYPE = 2
    DATE = 3


# pylint: disable=too-many-public-methods
class TreeView(QTreeView):
    def __init__(self, parent, tree_model: Tree, last_selected_path: str = None):
        super().__init__(parent)
        self.last_selected_path = last_selected_path
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

    def init_ui(self):
        self.setStyleSheet(
            """QToolTip {background-color: black;
                                  color: gray;
                                  border: lightGray solid 1px
                                  }"""
        )
        self.setToolTipDuration(5000)
        self.hide_header(hide=self.tree_model.hide_header)
        for column in TreeColumn:
            self.hide_column(column=column.value, hide=column.value not in self.tree_model.visible_columns)
        self.sys_model.directoryLoaded.connect(self.on_dir_loaded)
        self.sys_model.setRootPath(None)
        self.pinned_path = self.tree_model.pinned_path
        if self.tree_model.current_path:
            self.current_path = self.tree_model.current_path
        self.filter = self.get_filter()
        self.setAcceptDrops(True)
        self.setDragEnabled(True)
        self.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.setContextMenuPolicy(Qt.CustomContextMenu)

        self.clicked.connect(self.on_clicked)
        self.activated.connect(self.on_activated)
        self.customContextMenuRequested.connect(self.open_menu)

    def selectionChanged(self, selected: QItemSelection, deselected: QItemSelection) -> None:
        super().selectionChanged(selected, deselected)
        # app = self.main_form.app_qt_object
        # logger.info(f"is active {app.activeWindow()} {app.focusWidget()}")
        # if app.activeWindow() != 0 and app.focusWidget() != 0:
        #     self.setFocus()

    def drawRow(self, painter: QPainter, options: QStyleOptionViewItem, index: QModelIndex) -> None:
        new_options = QStyleOptionViewItem(options)
        sys_index = self.sys_index(proxy_index=index)
        file_path = self.sys_model.filePath(sys_index)
        info = QFileInfo(file_path)
        if info.isHidden():
            new_options.palette.setColor(QPalette.Text, Qt.darkGray)
        super().drawRow(painter, new_options, index)

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

    def path_from_tree_index(self, proxy_index: QModelIndex):
        return self.sys_model.fileInfo(self.sys_index(proxy_index=proxy_index)).absoluteFilePath()

    @property
    def current_path(self) -> Optional[str]:
        if self.currentIndex().isValid():
            return self.path_from_tree_index(proxy_index=self.currentIndex())
        return None

    @current_path.setter
    def current_path(self, path: str):
        if path:
            parent_path = path_util.parent_path(path=path)
            sys_index = self.sys_model.index(parent_path)
            if sys_index.isValid():
                self.expand(sys_index)
            sys_index = self.sys_model.index(path)
            if sys_index.isValid():
                index = self.proxy_index(sys_index=sys_index)
                self.setCurrentIndex(index)
                selection_model = self.selectionModel()
                selection_model.select(index, selection_model.Clear | selection_model.Select | selection_model.Current)
                self.scrollTo(index, QAbstractItemView.ScrollHint.PositionAtCenter)
            else:
                logger.debug(f"Invalid path {path}")
        self.tree_model.current_path = path

    def set_selection(self, selection: List[str] = None):
        logger.debug(
            f"{path_caption(self.current_path)} "
            f"selection {selection} "
            f"has selection {self.selectionModel().hasSelection()} "
            f"valid {self.rootIndex().isValid()}"
        )
        if selection is None and not self.selectionModel().hasSelection():
            if self.rootIndex() and self.rootIndex().isValid():
                self.current_path = self.current_path  # self.path_from_tree_index(proxy_index=self.rootIndex())
                logger.debug(f"SELECTING {self.current_path}")
            else:
                logger.debug("rootIndex() not set")
        elif selection:
            if len(selection) > 0:
                self.current_path = selection[0]
            # else:
            #     raise RuntimeError(f"Only one selection supported {selection}")

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
                    self.restore_layout()
                    self.set_selection(selection=[self.last_selected_path] if self.last_selected_path else [path])
                    logger.debug(f"should be selected {[path]}")
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

    def get_filter(self) -> QDir.Filters:
        files, hidden, system = self.tree_model.show_files, self.tree_model.show_hidden, self.tree_model.show_system
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

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.accept()
        else:
            event.ignore()

    def dragMoveEvent(self, event: QDragMoveEvent):
        index = self.indexAt(event.pos())
        path = self.sys_model.fileInfo(self.proxy.mapToSource(index)).absoluteFilePath()
        logger.debug(f"Drop action {event.dropAction()} {path}")
        if event.mimeData().hasUrls:
            event.accept()
        else:
            event.ignore()

    def dropEvent(self, event: QDropEvent):
        modifiers = event.keyboardModifiers()
        func = copy if modifiers == Qt.ShiftModifier else move
        files = [u.toLocalFile() for u in event.mimeData().urls()]
        index = self.indexAt(event.pos())
        path = self.sys_model.fileInfo(self.proxy.mapToSource(index)).absoluteFilePath()
        logger.debug(f"dropped files {files} action {func}")
        if files and path:
            run_in_thread(
                parent=self,
                target=func,
                args=[files, path, False],
                threads=self.main_form.threads,
            )
            logger.debug(f"action executed {func} files {files}")

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

    def store_layout(self):
        expanded = []
        for index in self.proxy.persistentIndexList():
            if self.isExpanded(index):
                expanded.append(str(index.data(Qt.DisplayRole)))
        self.tree_model.expanded_items = expanded
        self.tree_model.last_selected_path = self.current_path

    def restore_layout(self):
        self.setUpdatesEnabled(False)
        logger.debug(f"expanding {self.tree_model.expanded_items} for {self.pinned_path} {self.tree_model.pinned_path}")
        self.expand_items(expanded_items=self.tree_model.expanded_items, start_index=self.rootIndex())
        self.setUpdatesEnabled(True)

    def expand_items(self, expanded_items: List[str], start_index: QModelIndex):
        for expanded in expanded_items:
            matches = self.proxy.match(start_index, Qt.DisplayRole, expanded)
            for index in matches:
                logger.debug(f"expanding index {start_index.data(Qt.DisplayRole)}")
                self.expand(index)
                self.expand_items(expanded_items, self.proxy.index(0, 0, index))


class SortFilterModel(QSortFilterProxyModel):
    def lessThan(self, left, right):
        left_path = self.sourceModel().filePath(left)
        right_path = self.sourceModel().filePath(right)
        return (not os.path.isdir(left_path), left_path.lower()) < (not os.path.isdir(right_path), right_path.lower())

    def data(self, index: QModelIndex, role: int = ...) -> Any:
        if role == Qt.ToolTipRole:
            sys_index = self.mapToSource(index)
            file_path = self.sourceModel().filePath(sys_index)
            info = QFileInfo(file_path)
            last_modified = info.lastModified().toString("yyyy/MM/dd hh:mm:ss")
            modifiers = QApplication.keyboardModifiers()
            parts = []
            if modifiers == Qt.ShiftModifier:
                if info.isFile():
                    parts = file_first_lines(file_path=info.absoluteFilePath(), count=20)
                elif info.isDir():
                    parts = dir_list(path=info.absoluteFilePath())
            else:
                parts = [f"Path: {info.absoluteFilePath()}", f"Last modified: {last_modified}"]
                if info.isFile():
                    parts.append(f"Size: {convert_size(info.size())}")
            return "\n".join(parts)
        return super().data(index, role)
