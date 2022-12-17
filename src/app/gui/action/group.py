from enum import Enum
from typing import Callable

from PySide2.QtCore import Qt
from PySide2.QtGui import QKeySequence
from PySide2.QtWidgets import QWidget

from src.app.gui.action.command import Action


class GroupAction(str, Enum):
    NEW = "New group"
    RENAME = "Rename group"
    CLOSE_ALL = "Close all groups"
    CLOSE_OTHER = "Close other groups"
    CLOSE = "Close group"


def create_new_group_action(parent: QWidget) -> Action:
    return Action(
        parent=parent,
        caption=GroupAction.NEW,
        shortcut=QKeySequence(Qt.CTRL + Qt.SHIFT + Qt.Key_G),
        slot=parent.new_group,
    )


def create_close_all_groups_action(parent_func: Callable) -> Action:
    return Action(
        parent=parent_func().main_form,
        caption=GroupAction.CLOSE_ALL.value,
        shortcut=QKeySequence(Qt.CTRL + Qt.Key_F4),
        slot=lambda: parent_func().close_all_pages(),
    )


def create_close_group_action(parent_func: Callable, index_func: Callable) -> Action:
    return Action(
        parent=parent_func().main_form,
        caption=GroupAction.CLOSE.value,
        shortcut=QKeySequence(Qt.SHIFT + Qt.CTRL + Qt.Key_T),
        slot=lambda: parent_func().close_page(index_func=index_func),
    )
