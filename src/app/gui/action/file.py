from enum import Enum
from functools import partial
from typing import Callable

from PySide6.QtCore import Qt
from PySide6.QtGui import QKeySequence

import src.app.utils.file_util
from src.app.gui.action.command import Action
from src.app.utils import path_util
from src.app.utils.shell import start_file


class FileAction(Enum):
    CREATE = "Create file"
    CREATE_CLIP = "Create from clipboard text"
    OPEN = "Open file"
    OPEN_VS = "Open (VS Code)"


def create_file_action(parent_func: Callable, path_func: Callable) -> Action:
    return Action(
        parent=parent_func().main_form,
        caption=FileAction.CREATE.value,
        shortcut=QKeySequence(Qt.CTRL | Qt.Key_N),
        slot=partial(src.app.utils.file_util.create_file, parent_func, path_func),
        tip="Creates new file under current folder",
    )


def create_file_from_clipboard_text_action(parent_func: Callable, path_func: Callable) -> Action:
    return Action(
        parent=parent_func().main_form,
        caption=FileAction.CREATE_CLIP.value,
        shortcut=QKeySequence(Qt.CTRL | Qt.SHIFT | Qt.Key_V),
        slot=partial(src.app.utils.file_util.create_text_file_from_clip, parent_func, path_func),
        tip="Creates new file from clipboard text under current folder",
    )


def create_open_file_action(parent_func: Callable, path_func: Callable) -> Action:
    def open_paths():
        for path in path_util.only_files(paths=path_func()):
            start_file(file_name=path)

    return Action(
        parent=parent_func().main_form,
        caption=FileAction.OPEN.value,
        shortcut=None,
        slot=open_paths,
        tip="Opens selected file",
    )
