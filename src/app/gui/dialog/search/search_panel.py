from __future__ import annotations

import logging
from enum import Enum
from typing import List, Dict, NamedTuple

from PySide2.QtCore import QThread, Signal, QObject, Qt
from PySide2.QtGui import QFontMetrics
from PySide2.QtWidgets import (
    QWidget,
    QFormLayout,
    QComboBox,
    QCheckBox,
    QBoxLayout,
    QLineEdit,
    QPushButton,
    QLabel,
    QProgressBar,
    QMessageBox,
)

from src.app.gui.dialog.base import PathEdit
from src.app.gui.dialog.search.search_tree import SearchTree, SearchStat
from src.app.gui.widget import widget_of_widgets
from src.app.model.search import (
    SearchParam,
    SearchConfig,
    SearchState,
    FileSearchResultList,
    open_file,
)
from src.app.utils.constant import APP_NAME
from src.app.utils.logger import get_console_logger
from src.app.utils.path_util import path_caption
from src.app.utils.search import search, search_file
from src.app.utils.thread import ThreadWithWorker

logger = get_console_logger(__name__, log_level=logging.ERROR)


class SearchButtonCaption(str, Enum):
    SEARCH = "Search"
    CANCEL = "Cancel"


class SearchButton(QPushButton):
    def __init__(self, caption: str, search_panel: SearchPanel, parent: QWidget | None = None):
        super().__init__(caption, parent)
        self.search_panel = search_panel

    def set_state(self, search_state: SearchState):
        if search_state in (SearchState.READY, SearchState.COMPLETED):
            self.setText(SearchButtonCaption.SEARCH.value)
            self.setEnabled(True)
            self.search_panel.enable_search_controls(enabled=True)
        elif search_state == SearchState.RUNNING:
            self.setText(SearchButtonCaption.CANCEL.value)
            self.setEnabled(True)
            self.search_panel.enable_search_controls(enabled=False)
        elif search_state == SearchState.CANCELLED:
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
    return [part.strip() for part in text.split(";")]


class SearchPanel(QWidget):
    def __init__(self, path: str, parent, mf):
        super().__init__(parent=parent)
        self.search_control = parent
        self.main_form = mf
        self.form = QFormLayout()
        self.form.setLabelAlignment(Qt.AlignRight)
        self.form.setContentsMargins(10, 10, 10, 10)
        self.form.setSpacing(5)

        self.thread_with_worker: ThreadWithWorker | None = None

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

        # Progress
        self.status = QLabel()
        self.progress = QProgressBar()

        # Form
        self.form.addRow("Containing text", self.keyword_search)
        self.form.addRow("Mask", self.widget_map["name_filters"])
        self.form.addRow("Path", self.widget_map["path"])
        self.form.addRow("Excluded dirs", self.widget_map["excluded_dirs"])
        self.form.addRow("", self.widget_map["ignore_case"])
        self.form.addRow("", self.widget_map["whole_words"])
        self.form.addRow("", self.widget_map["subdirectories"])
        self.form.addRow("", self.widget_map["reg_exp"])

        self.form.addRow("Status", self.status)
        self.form.addRow("Progress", self.progress)

        # Search stat label
        # self.search_status_label = QLabel()

        # Search tree
        self.search_tree = SearchTree(parent=self, mf=mf)

        self.main_layout = QBoxLayout(QBoxLayout.TopToBottom, self)
        self.main_layout.addLayout(self.form)
        # self.main_layout.addWidget(self.search_status_label)
        self.main_layout.addWidget(self.search_tree)

        self.setLayout(self.main_layout)

        self.search_btn.clicked.connect(self.search_action)

    def set_status(self, text: str):
        metrics = QFontMetrics(self.status.font())
        elided_text = metrics.elidedText(text, Qt.ElideMiddle, self.status.width())
        self.status.setText(elided_text)

    def reset_progress(self):
        self.progress.setRange(0, 100)
        self.progress.reset()
        self.progress.setTextVisible(False)

    def reset_search_thread(self):
        logger.debug("excuting reset_search")
        self.main_form.remove_thread(thread_with_worker=self.thread_with_worker)
        self.thread_with_worker.thread.deleteLater()
        self.thread_with_worker = None

    def enable_search_controls(self, enabled: bool):
        for control in self.widget_map.values():
            control.setEnabled(enabled)

    def search_path(self) -> str:
        return self.widget_map["path"].text()

    def search_path_caption(self) -> str:
        return path_caption(path=self.search_path())

    def cancel_search(self):
        if self.thread_with_worker.thread and self.thread_with_worker.thread.isRunning():
            self.thread_with_worker.thread.requestInterruption()
            self.search_btn.set_state(search_state=SearchState.CANCELLED)

    def search_action(self):
        if self.thread_with_worker and self.thread_with_worker.thread and self.thread_with_worker.thread.isRunning():
            self.cancel_search()
            return
        self.search()

    def search_on_started(self, search_param: SearchParam):
        self.search_btn.set_state(search_state=SearchState.RUNNING)
        self.search_tree.pre_search_actions(search_param=search_param)

    def search_on_progress_status(self, progress_status: ProgressStatus):
        self.set_status(text=progress_status.status)
        self.progress.setTextVisible(True)
        self.progress.setRange(progress_status.progress_min, progress_status.progress_max)
        self.progress.setValue(progress_status.progress_value)
        self.progress.text = progress_status.progress_text
        # self.main_form.app_qt_object.processEvents()

    def search_on_progress(self, file_search_result_list: FileSearchResultList):
        if file_search_result_list:
            self.set_status(text="Processing results - please wait")
        # self.main_form.app_qt_object.processEvents()
        self.search_tree.process_result_list(file_search_result_list=file_search_result_list)

    def search_on_exception(self, message: str):
        self.set_status(text=message)
        self.reset_progress()
        self.search_tree.clear_tree()
        QMessageBox.information(self.main_form, APP_NAME, message)

    def search_on_user_exception(self, message: str):
        self.set_status(text=message)
        self.reset_progress()
        self.search_tree.clear_tree()

    def search_on_finished(self, search_stat: SearchStat):
        self.search_post_actions(search_stat=search_stat)
        self.search_btn.set_state(search_state=SearchState.READY)

    def search_post_actions(self, search_stat: SearchStat):
        if search_stat:
            text = f"Found {str(search_stat.dirs)} folders and {str(search_stat.files)} files"
            self.set_status(text=text)

    def search(self):
        search_param = self.get_search_param()
        # self.search_on_started(search_param=search_param)
        search_thread = QThread()
        search_worker = SearchWorker(search_param=search_param)
        self.thread_with_worker = ThreadWithWorker(thread=search_thread, worker=search_worker)
        search_worker.moveToThread(search_thread)
        search_thread.started.connect(search_worker.run)
        search_worker.finished.connect(search_thread.quit)
        search_worker.finished.connect(search_worker.deleteLater)
        search_thread.finished.connect(self.reset_search_thread)
        search_worker.started.connect(self.search_on_started)
        search_worker.progress_status.connect(self.search_on_progress_status)
        search_worker.progress.connect(self.search_on_progress)
        search_worker.finished.connect(self.search_on_finished)
        search_worker.exception.connect(self.search_on_exception)
        search_worker.user_exception.connect(self.search_on_user_exception)
        # Start the thread
        search_thread.start()
        self.main_form.threads.append(self.thread_with_worker)

    def get_search_param(self) -> SearchParam:
        search_param = {}
        for key, widget in self.widget_map.items():
            if isinstance(widget, QLineEdit):
                search_param[key] = widget.text()
            elif isinstance(widget, EditableComboBox):
                if key == "path":
                    search_param[key] = widget.currentText()
                else:
                    search_param[key] = split_multiple_values(text=widget.currentText())
            elif isinstance(widget, QCheckBox):
                search_param[key] = widget.isChecked()
        return SearchParam(**search_param)


class ProgressStatus(NamedTuple):
    status: str = ""
    progress_min: int = 0
    progress_max: int = 0
    progress_value: int = 0

    def progress_text(self) -> str:
        if self.progress_min == 0 and self.progress_max == 0:
            return ""
        percent = 0
        if self.progress_value > 0:
            percent = round(
                round((self.progress_value - self.progress_min) / (self.progress_max - self.progress_min), 2) * 100
            )
        return f"Processed {str(self.progress_value)} of {str(self.progress_max)} files ({str(percent)}%)"


class UserInterruptionRequest(Exception):
    pass


class SearchWorker(QObject):
    started = Signal(SearchParam)
    progress = Signal(FileSearchResultList)
    progress_status = Signal(ProgressStatus)
    finished = Signal(SearchStat)
    exception = Signal(str)
    user_exception = Signal(str)

    def __init__(self, search_param: SearchParam):
        super().__init__()
        self.search_param = search_param

    def check_if_user_requested_cancel(self):
        QThread.currentThread().usleep(1)
        if QThread.currentThread().isInterruptionRequested():
            logger.debug("TERMINATED")
            raise UserInterruptionRequest("Cancelled")

    def run(self):
        try:
            logger.debug("search init")
            self.started.emit(self.search_param)
            result_buffer = []
            search_results = []
            for search_result in search(search_param=self.search_param):
                self.check_if_user_requested_cancel()
                self.progress_status.emit(ProgressStatus(status=search_result.file_name))
                search_results.append(search_result)
            search_results_count = len(search_results)
            search_stat = SearchStat(dirs=0, files=0, hits=0)
            logger.debug("search started")
            for index in range(search_results_count):
                self.check_if_user_requested_cancel()
                self.progress_status.emit(
                    ProgressStatus(
                        status=search_results[index].file_name,
                        progress_max=search_results_count,
                        progress_value=index + 1,
                    )
                )
                if search_results[index].is_dir:
                    search_stat.dirs += 1
                else:
                    search_stat.files += 1
                if not search_results[index].is_dir and self.search_param.keyword:
                    text_lines = open_file(file_name=search_results[index].file_name)
                    search_results[index] = search_file(
                        search_param=self.search_param, text_lines=text_lines, search_result=search_results[index]
                    )
                if (
                    search_results[index].error is not None
                    or search_results[index].hits is not None
                    or not self.search_param.keyword
                ):
                    result_buffer.append(search_results[index])
                    # self.progress.emit(FileSearchResultList(__root__=result_buffer))
                    # QThread.currentThread().usleep(1)
                    # result_buffer = []
                if search_results[index].error:
                    logger.error(search_results[index].error)
            logger.debug("search finished - processing results")
            self.progress.emit(FileSearchResultList(__root__=result_buffer))
            logger.debug("results processed")
            self.finished.emit(search_stat)
        except UserInterruptionRequest as e:
            self.user_exception.emit(str(e))
            self.finished.emit(None)
        except Exception as e:
            logger.error(str(e))
            self.exception.emit(str(e))
            self.finished.emit(None)
