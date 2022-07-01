import copy
from typing import List

from PySide2.QtWidgets import QWidget, QFormLayout, QComboBox, QCheckBox, QBoxLayout, QLineEdit, QPushButton, QLabel

from src.app.gui.dialog.base import PathEdit
from src.app.gui.dialog.search.search_tree import SearchTree
from src.app.gui.widget import widget_of_widgets
from src.app.model.search import SearchParam, SearchConfig
from src.app.utils.path_util import path_caption
from src.app.utils.search import search


class EditableComboBox(QComboBox):
    def __init__(self, items: List[str], text: str = None):
        super().__init__()
        self.setEditable(True)
        self.addItems(items)
        self.setCurrentIndex(0)
        if text:
            self.setCurrentText(text)


def split_multiple_values(text: str) -> List[str]:
    if ";" not in text:
        return [text]
    return text.split(";")


class SearchPanel(QWidget):
    def __init__(self, path: str, parent, mf):
        super().__init__(parent=parent)
        self.search_control = parent
        self.form = QFormLayout()
        self.form.setContentsMargins(10, 10, 10, 10)
        self.form.setSpacing(5)

        self.search_param = SearchParam()
        self.widget_map = {key: None for key in self.search_param.dict().keys()}

        self.widget_map["keyword"] = QLineEdit()
        self.widget_map["keyword"].setStyleSheet("color: gold")
        self.search_btn = QPushButton("Search")
        self.keyword_search = widget_of_widgets(
            direction=QBoxLayout.LeftToRight, widgets=[self.widget_map["keyword"], self.search_btn]
        )
        self.search_config = SearchConfig()
        self.widget_map["name_filters"] = EditableComboBox(self.search_config.name_filters)
        self.widget_map["path"] = PathEdit(text=path, post_action=lambda x: self.search_control.rename_tab(self))
        self.widget_map["excluded_dirs"] = EditableComboBox(self.search_config.excluded_dirs)
        self.widget_map["ignore_case"] = QCheckBox("Ignore case")
        self.widget_map["ignore_case"].setChecked(True)
        self.widget_map["whole_words"] = QCheckBox("Whole words")
        self.widget_map["subdirectories"] = QCheckBox("Including subdirectories")
        self.widget_map["subdirectories"].setChecked(True)
        self.widget_map["reg_exp"] = QCheckBox("Regular expression")

        # Form
        self.form.addRow("Containing text", self.keyword_search)
        self.form.addRow("Mask", self.widget_map["name_filters"])
        self.form.addRow("Path", self.widget_map["path"])
        self.form.addRow("Excluded dirs", self.widget_map["excluded_dirs"])
        self.form.addRow("", self.widget_map["ignore_case"])
        self.form.addRow("", self.widget_map["whole_words"])
        self.form.addRow("", self.widget_map["subdirectories"])
        self.form.addRow("", self.widget_map["reg_exp"])

        # Search stat label
        self.search_stat_label = QLabel()

        # Search tree
        self.search_tree = SearchTree(parent=self, mf=mf)

        self.main_layout = QBoxLayout(QBoxLayout.TopToBottom, self)
        self.main_layout.addLayout(self.form)
        self.main_layout.addWidget(self.search_stat_label)
        self.main_layout.addWidget(self.search_tree)

        self.setLayout(self.main_layout)

        self.search_btn.clicked.connect(self.search_action)

    def search_path(self) -> str:
        return self.widget_map["path"].text()

    def search_path_caption(self) -> str:
        return path_caption(path=self.search_path())

    def search_action(self):
        self.search()

    def search(self):
        search_param = self.get_search_param()
        print(search_param)
        search_results = search(search_param=search_param)
        self.search_tree.process_results(search_param=search_param, results=search_results)

    def get_search_param(self) -> SearchParam():
        search_param = {}
        for key, widget in self.widget_map.items():
            match widget:
                case QLineEdit() as edit:
                    search_param[key] = edit.text()
                case EditableComboBox() as combo:
                    if key == "path":
                        search_param[key] = combo.currentText()
                    else:
                        search_param[key] = split_multiple_values(text=combo.currentText())
                case QCheckBox() as check:
                    search_param[key] = check.isChecked()
        return SearchParam(**search_param)

