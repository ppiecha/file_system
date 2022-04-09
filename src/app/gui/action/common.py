from enum import Enum
from typing import Callable

from PySide2.QtGui import QIcon, QKeySequence, Qt
from PySide2.QtWidgets import QAction, QMenu, QWidget

from src.app.utils.path_util import copy_items_to_clipboard, paste_items_from_clipboard, cut_items_to_clipboard, \
    delete_items
from src.app.utils.logger import get_console_logger

logger = get_console_logger(name=__name__)


class CommonAction(str, Enum):
    CUT = "Cut"
    COPY = "Copy"
    COPY_TO = "Copy to..."
    MOVE_TO = "Move to..."
    PASTE = "Paste"
    DELETE = "Delete"
    RENAME = "Rename"
    DUPLICATE = "Duplicate"
    COMPARE = "Compare/Diff"


class Action(QAction):
    def __init__(
        self,
        parent: QMenu,
        caption: str = None,
        icon: QIcon = None,
        shortcut=None,
        slot: Callable = None,
        tip=None,
        status_tip=None,
    ):
        super().__init__(caption, parent)
        if icon:
            self.setIcon(icon)
        if isinstance(shortcut, list):
            self.setShortcuts(shortcut)
        else:
            self.setShortcut(shortcut)
        self.setToolTip(tip or caption)
        self.setStatusTip(status_tip or caption)
        if slot:
            self.triggered.connect(slot)


def create_action(parent: QWidget, caption: str, slot: callable, shortcut: QKeySequence, tip: str):
    return Action(
        parent=parent,
        caption=caption,
        shortcut=shortcut,
        slot=slot,
        tip=tip,
    )


def create_cut_items_to_clipboard_action(parent_func: Callable, path_func: Callable) -> Action:
    return Action(
        parent=parent_func().main_form,
        caption=CommonAction.CUT.value,
        shortcut=Qt.CTRL + Qt.Key_X,
        slot=lambda: cut_items_to_clipboard(parent=parent_func().main_form, path_func=path_func),
        tip="Cut item to clipboard",
    )


def create_copy_items_to_clipboard_action(parent_func: Callable, path_func: Callable) -> Action:
    return Action(
        parent=parent_func().main_form,
        caption=CommonAction.COPY.value,
        shortcut=Qt.CTRL + Qt.Key_C,
        slot=lambda: copy_items_to_clipboard(parent=parent_func(), path_func=path_func),
        tip="Copies selected items to clipboard",
    )


def create_paste_items_from_clipboard_action(parent_func: Callable, path_func: Callable) -> Action:
    return Action(
        parent=parent_func().main_form,
        caption=CommonAction.PASTE.value,
        shortcut=Qt.CTRL + Qt.Key_V,
        slot=lambda: paste_items_from_clipboard(parent=parent_func().main_form, path_func=path_func),
        tip="Paste item from clipboard into selected path",
    )


def create_delete_items_action(parent_func: Callable, path_func: Callable) -> Action:
    return Action(
        parent=parent_func().main_form,
        caption=CommonAction.DELETE.value,
        shortcut=[QKeySequence(Qt.Key_Delete), QKeySequence(Qt.CTRL + Qt.Key_Delete)],
        slot=lambda: delete_items(parent=parent_func().main_form, path_func=path_func),
        tip="Deletes selected items",
    )