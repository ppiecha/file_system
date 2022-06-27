from typing import Iterator

from PySide2.QtCore import Qt
from PySide2.QtWidgets import QTreeWidget, QAbstractItemView, QTreeWidgetItem, QLabel

from src.app.model.search import FileSearchResult


class SearchTree(QTreeWidget):
    def __init__(self, parent, mf):
        super().__init__(parent=parent)
        self.init_ui()

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

    def process_results(self, results: Iterator[FileSearchResult]):
        self.clear()
        for result in [result for result in results if result.error is None]:
            file_item = QTreeWidgetItem(self)
            # file_item.setText(0, result.as_html())
            self.setItemWidget(file_item, 0, QLabel(result.as_html()))
            file_item.setData(0, Qt.UserRole, result)
            for hit in result.hit_iter():
                line_item = QTreeWidgetItem(file_item)
                # line_item.setText(0, hit.as_html())
                line_item.setData(0, Qt.UserRole, hit)
                self.setItemWidget(line_item, 0, QLabel(hit.as_html()))
