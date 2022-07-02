import dataclasses
from typing import Iterator, NamedTuple

from PySide2.QtCore import Qt
from PySide2.QtWidgets import QTreeWidget, QAbstractItemView, QTreeWidgetItem, QLabel, QStyle

from src.app.model.search import FileSearchResult, SearchParam, format_keyword


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

    def init_ui(self):
        self.setHeaderHidden(True)
        self.setSelectionMode(QAbstractItemView.SingleSelection)
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        # self.clicked.connect(self.on_clicked)
        # self.doubleClicked.connect(self.on_double_clicked)
        # self.itemActivated.connect(self.on_item_activated)
        # self.customContextMenuRequested.connect(self.open_menu)
        # self.itemExpanded.connect(self.expanded)
        # self.itemCollapsed.connect(self.collapsed)
        # self.itemSelectionChanged.connect(self.selection_changed)

    def process_result(self, file_search_result: FileSearchResult):
        file_item = QTreeWidgetItem(self)
        self.setItemWidget(file_item, 0, QLabel(file_search_result.as_html()))
        file_item.setData(0, Qt.UserRole, file_search_result)
        file_item.setIcon(0, file_search_result.icon())
        for hit in file_search_result.hit_iter():
            line_item = QTreeWidgetItem(file_item)
            line_item.setData(0, Qt.UserRole, hit)
            hit_label = QLabel(hit.as_html())
            line_item.setSizeHint(0, hit_label.sizeHint())
            self.setItemWidget(line_item, 0, hit_label)

    def add_search_info_node(self, search_param: SearchParam):
        search_header = QTreeWidgetItem(self)
        self.setItemWidget(search_header, 0, QLabel(search_param.as_html()))

    def pre_search_actions(self, search_param: SearchParam):
        self.clear()
        self.add_search_info_node(search_param=search_param)

    def post_search_actions(self, search_stat: SearchStat):
        hits = ""
        # if search_param.keyword:
        #     hits = format_keyword(keyword=f"hits {str(search_stat.hits)}")
        text = f"Folders {str(search_stat.dirs)} files {str(search_stat.files)} {hits}"
        self.search_panel.search_status_label.setText(text)
