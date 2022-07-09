import dataclasses
from typing import List, Dict

from PySide2.QtCore import Qt
from PySide2.QtWidgets import QTreeWidget, QAbstractItemView, QTreeWidgetItem, QLabel, QMenu, QHeaderView

from src.app.gui.action.command import CommonAction
from src.app.gui.action.file import FileAction
from src.app.gui.action.folder import FolderAction
from src.app.gui.action.selection import SelectionAction
from src.app.model.search import SearchParam, FileSearchResultList, LineHit
from src.app.utils import path_util
from src.app.utils.logger import get_console_logger

logger = get_console_logger(__name__)


@dataclasses.dataclass
class SearchStat:
    dirs: int
    files: int
    hits: int


class SearchTree(QTreeWidget):
    def __init__(self, parent, mf):
        super().__init__(parent=parent)
        self.init_ui()
        self.search_panel = parent
        self.main_form = mf

    def init_ui(self):
        self.setHeaderHidden(True)
        self.header().setStretchLastSection(False)
        self.header().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        # self.clicked.connect(self.on_clicked)
        # self.doubleClicked.connect(self.on_double_clicked)
        # self.itemActivated.connect(self.on_item_activated)
        self.customContextMenuRequested.connect(self.open_menu)
        # self.itemExpanded.connect(self.expanded)
        # self.itemCollapsed.connect(self.collapsed)
        # self.itemSelectionChanged.connect(self.selection_changed)

    # def process_result(self, file_search_result: FileSearchResult):
    #     file_item = QTreeWidgetItem(self)
    #     self.setItemWidget(file_item, 0, QLabel(file_search_result.as_html()))
    #     file_item.setData(0, Qt.UserRole, file_search_result)
    #     file_item.setIcon(0, self.main_form.get_icon(res=file_search_result))
    #     for hit in file_search_result.hit_iter():
    #         line_item = QTreeWidgetItem(file_item)
    #         line_item.setData(0, Qt.UserRole, hit)
    #         hit_label = QLabel(hit.as_html())
    #         line_item.setSizeHint(0, hit_label.sizeHint())
    #         self.setItemWidget(line_item, 0, hit_label)

    def process_result_list(self, file_search_result_list: FileSearchResultList):
        self.setColumnCount(1)
        items = []
        for file_search_result in file_search_result_list:
            self.main_form.app_qt_object.processEvents()
            file_item = QTreeWidgetItem(self)
            file_item.setData(0, Qt.UserRole, file_search_result)
            file_item.setIcon(0, self.main_form.get_icon(res=file_search_result))
            file_label = QLabel(file_search_result.as_html())
            file_item.setSizeHint(0, file_label.sizeHint())
            self.setItemWidget(file_item, 0, file_label)
            for hit in file_search_result.hit_iter():
                line_item = QTreeWidgetItem(file_item)
                line_item.setData(0, Qt.UserRole, hit)
                hit_label = QLabel(hit.as_html())
                line_item.setSizeHint(0, hit_label.sizeHint())
                self.setItemWidget(line_item, 0, hit_label)
            items.append(file_item)
        self.addTopLevelItems(items)

        # for file_search_result in file_search_result_list:
        #     self.process_result(file_search_result=file_search_result)
        # self.main_form.app_qt_object.processEvents()

    def add_search_info_node(self, search_param: SearchParam):
        search_header = QTreeWidgetItem(self)
        self.setItemWidget(search_header, 0, QLabel(search_param.as_html()))

    def pre_search_actions(self, search_param: SearchParam):
        self.clear()
        self.add_search_info_node(search_param=search_param)

    def clear_tree(self):
        self.clear()

    def get_selected_paths(self) -> List[str]:
        return [item.data(0, Qt.UserRole).file_name for item in self.selectedItems()]

    def get_paths_with_hits(self) -> Dict[str, LineHit]:
        if self.search_panel.search_control.search_dlg.isActiveWindow():
            return {
                item.data(0, Qt.UserRole).file_name: item.data(0, Qt.UserRole)
                for item in self.selectedItems()
                if isinstance(item.data(0, Qt.UserRole), LineHit)
            }
        return {}

    def open_menu(self, position):
        paths = self.get_selected_paths()
        logger.debug(f"selected search paths {paths}")
        if paths is not None and len(paths) > 0:
            menu = QMenu()
            if path_util.all_files(paths=paths):
                menu.addAction(self.main_form.actions[FileAction.OPEN])
            menu.addAction(self.main_form.actions[FolderAction.OPEN_EXT])
            menu.addAction(self.main_form.actions[FolderAction.OPEN_TAB])
            menu.addAction(self.main_form.actions[FolderAction.OPEN_CONSOLE])
            menu.addSeparator()
            menu.addAction(self.search_panel.search_control.search_actions["go_to_item"])
            menu.addAction(self.main_form.actions[CommonAction.VIEW])
            menu.addAction(self.main_form.actions[CommonAction.EDIT])
            menu.addAction(self.main_form.actions[CommonAction.PROPERTIES])
            sel_menu = QMenu("Copy selected")
            sel_menu.addAction(self.main_form.actions[SelectionAction.COPY_PATH])
            sel_menu.addAction(self.main_form.actions[SelectionAction.COPY_PATH_WITH_NAME])
            sel_menu.addAction(self.main_form.actions[SelectionAction.COPY_NAME])
            menu.addMenu(sel_menu)
            menu.exec_(self.viewport().mapToGlobal(position))
