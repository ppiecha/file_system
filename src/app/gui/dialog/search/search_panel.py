from PySide2.QtWidgets import QWidget, QFormLayout, QComboBox, QCheckBox, QBoxLayout

from src.app.gui.dialog.search.search_tree import SearchTree
from src.app.model.search import SearchParam
from src.app.utils.search import search


class SearchPanel(QWidget):
    def __init__(self, path: str, parent, mf):
        super().__init__(parent=parent)
        self.form = QFormLayout()
        self.form.setContentsMargins(10, 10, 10, 10)
        self.form.setSpacing(5)
        self.keyword_box = QComboBox()
        self.keyword_box.setEditable(True)
        self.mask_box = QComboBox()
        self.path_box = QComboBox()
        self.excluded_dirs_box = QComboBox()
        self.ignore_case_box = QCheckBox("Ignore case")
        self.whole_words_box = QCheckBox("Whole words")
        self.subdirectories_box = QCheckBox("Including subdirectories")
        self.reg_exp_box = QCheckBox("Regular expression")

        self.search_tree = SearchTree(parent=self, mf=mf)

        # Form
        self.form.addRow("Containing text", self.keyword_box)
        self.form.addRow("Mask", self.mask_box)
        self.form.addRow("Path", self.path_box)
        self.form.addRow("Excluded directories", self.excluded_dirs_box)
        self.form.addRow("", self.ignore_case_box)
        self.form.addRow("", self.whole_words_box)
        self.form.addRow("", self.subdirectories_box)
        self.form.addRow("", self.reg_exp_box)

        self.main_layout = QBoxLayout(QBoxLayout.TopToBottom, self)
        self.main_layout.addLayout(self.form)
        self.main_layout.addWidget(self.search_tree)

        self.setLayout(self.main_layout)

        search_param = SearchParam(keyword="False", path=r"C:/Users/piotr/_piotr_/__GIT__/Python/Navigator/util")
        search_results = search(search_param=search_param)
        self.search_tree.process_results(results=search_results)

    def get_search_param(self) -> SearchParam:
        pass
