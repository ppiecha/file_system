from enum import Enum
from typing import Callable

from PySide2.QtCore import QMimeData, QFileInfo, Qt
from PySide2.QtWidgets import QApplication

from src.app.gui.action.command import Action
from src.app.utils.logger import get_console_logger
from src.app.utils.path_util import extract_path, folder_name, file_name

logger = get_console_logger(name=__name__)


class SelectionAction(Enum):
    COPY_PATH = "Copy path"
    COPY_PATH_WITH_NAME = "Copy path with name"
    COPY_NAME = "Copy name"


def selected_names(path_func: Callable, mode: SelectionAction) -> bool:
    paths = path_func()
    clipboard = QApplication.clipboard()
    data = QMimeData()
    urls = []
    for path in paths:
        info = QFileInfo(path)
        if mode == SelectionAction.COPY_PATH:
            urls.append(extract_path(item=path))
        if mode == SelectionAction.COPY_PATH_WITH_NAME:
            if info.isDir():
                urls.append(path)
            else:
                urls.append(info.absoluteFilePath())
        if mode == SelectionAction.COPY_NAME:
            if info.isDir():
                urls.append(folder_name(path=path))
            else:
                urls.append(file_name(path=path))
    text = "\n".join(urls)
    logger.debug(f"selected items {text}")
    data.setText(text)
    clipboard.setMimeData(data)
    return True


def create_copy_path_action(parent_func: Callable, path_func: Callable) -> Action:
    return Action(
        parent=parent_func().main_form,
        caption=SelectionAction.COPY_PATH.value,
        shortcut=Qt.CTRL + Qt.SHIFT + Qt.Key_P,
        slot=lambda: selected_names(path_func=path_func, mode=SelectionAction.COPY_PATH),
        tip="Copies path(s)",
    )


def create_copy_path_with_name_action(parent_func: Callable, path_func: Callable) -> Action:
    return Action(
        parent=parent_func().main_form,
        caption=SelectionAction.COPY_PATH_WITH_NAME.value,
        shortcut=Qt.CTRL + Qt.SHIFT + Qt.Key_C,
        slot=lambda: selected_names(path_func=path_func, mode=SelectionAction.COPY_PATH_WITH_NAME),
        tip="Copies path(s) with name(s)",
    )


def create_copy_name_action(parent_func: Callable, path_func: Callable) -> Action:
    return Action(
        parent=parent_func().main_form,
        caption=SelectionAction.COPY_NAME.value,
        shortcut=Qt.SHIFT + Qt.Key_C,
        slot=lambda: selected_names(path_func=path_func, mode=SelectionAction.COPY_NAME),
        tip="Copies only name(s)",
    )
