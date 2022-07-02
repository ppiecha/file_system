from __future__ import annotations
from enum import Enum
from typing import List, Dict

from PySide2 import QtCore
from PySide2.QtCore import QThread, Signal, QObject
from PySide2.QtWidgets import QWidget, QFormLayout, QComboBox, QCheckBox, QBoxLayout, QLineEdit, QPushButton, QLabel, \
    QApplication

from src.app.gui.dialog.base import PathEdit
from src.app.gui.dialog.search.search_tree import SearchTree, SearchStat
from src.app.gui.widget import widget_of_widgets
from src.app.model.search import SearchParam, SearchConfig, SearchState, FileSearchResult
from src.app.utils.path_util import path_caption
from src.app.utils.search import search


class SearchButtonCaption(str, Enum):
    SEARCH = "Search"
    CANCEL = "Cancel"


class SearchButton(QPushButton):
    def __init__(self, caption: str, search_panel: SearchPanel, parent: QWidget | None = None):
        super().__init__(caption, parent)
        self.search_panel = search_panel

    def set_state(self, search_state: SearchState):
        match search_state:
            case SearchState.READY | SearchState.COMPLETED:
                self.setText(SearchButtonCaption.SEARCH.value)
                self.setEnabled(True)
                self.search_panel.enable_search_controls(enabled=True)
            case SearchState.RUNNING:
                self.setText(SearchButtonCaption.CANCEL.value)
                self.setEnabled(True)
                self.search_panel.enable_search_controls(enabled=False)
            case SearchState.CANCELLED:
                self.setText(SearchButtonCaption.CANCEL.value)
                self.setEnabled(False)
                self.search_panel.enable_search_controls(enabled=False)


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
        self.mf = mf
        self.form = QFormLayout()
        self.form.setContentsMargins(10, 10, 10, 10)
        self.form.setSpacing(5)

        # self.search_state = SearchState.READY
        self.search_thread: QThread | None = None
        self.search_worker: SearchWorker | None = None

        self.search_param = SearchParam()
        self.widget_map = {key: None for key in self.search_param.dict().keys()}

        self.widget_map: Dict[str, QWidget]
        self.widget_map["keyword"] = QLineEdit()
        self.widget_map["keyword"].setStyleSheet("color: gold")
        self.search_btn = SearchButton(caption=SearchButtonCaption.SEARCH.value, search_panel=self)
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
        self.search_status_label = QLabel()

        # Search tree
        self.search_tree = SearchTree(parent=self, mf=mf)

        self.main_layout = QBoxLayout(QBoxLayout.TopToBottom, self)
        self.main_layout.addLayout(self.form)
        self.main_layout.addWidget(self.search_status_label)
        self.main_layout.addWidget(self.search_tree)

        self.setLayout(self.main_layout)

        self.search_btn.clicked.connect(self.search_action)

    def reset_search_thread(self):
        self.search_thread = None

    def enable_search_controls(self, enabled: bool):
        for control in self.widget_map.values():
            control.setEnabled(enabled)

    def search_path(self) -> str:
        return self.widget_map["path"].text()

    def search_path_caption(self) -> str:
        return path_caption(path=self.search_path())

    def search_action(self):
        if self.search_thread and self.search_thread.isRunning():
            self.search_thread.requestInterruption()
            self.search_btn.set_state(search_state=SearchState.CANCELLED)
            return
        self.search()

    def search_on_started(self, search_param: SearchParam):
        self.search_btn.set_state(search_state=SearchState.RUNNING)
        self.search_tree.pre_search_actions(search_param=search_param)

    def search_on_progress(self, file_search_result: FileSearchResult):
        self.search_status_label.setText(file_search_result.file_name)
        self.search_tree.process_result(file_search_result=file_search_result)

    def search_on_finished(self, search_stat: SearchStat):
        self.search_tree.post_search_actions(search_stat=search_stat)
        self.search_btn.set_state(search_state=SearchState.READY)

    def search(self):
        search_param = self.get_search_param()
        self.search_on_started(search_param=search_param)
        self.search_thread = QThread()
        self.search_worker = SearchWorker(search_param=search_param)
        self.search_worker.moveToThread(self.search_thread)
        self.search_thread.started.connect(self.search_worker.run)
        self.search_worker.finished.connect(self.search_thread.quit)
        self.search_worker.finished.connect(self.search_worker.deleteLater)
        self.search_thread.finished.connect(self.search_thread.deleteLater)
        self.search_thread.finished.connect(self.reset_search_thread)
        self.search_worker.started.connect(self.search_on_started)
        self.search_worker.progress.connect(self.search_on_progress)
        self.search_worker.finished.connect(self.search_on_finished)
        # Start the thread
        self.search_thread.start()

    def get_search_param(self) -> SearchParam:
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


class SearchWorker(QObject):
    started = Signal(SearchParam)
    progress = Signal(FileSearchResult)
    finished = Signal(SearchStat)

    def __init__(self, search_param: SearchParam):
        super().__init__()
        self.search_param = search_param

    def run(self):
        # self.started.emit(self.search_param)
        search_results = search(search_param=self.search_param)
        search_stat = SearchStat(dirs=0, files=0, hits=0)
        for search_result in search_results:
            if QThread.currentThread().isInterruptionRequested():
                print("TERMINATED IN RUN")
                break
            if search_result.is_dir:
                search_stat.dirs += 1
            else:
                search_stat.files += 1
            self.progress.emit(search_result)
        self.finished.emit(search_stat)
