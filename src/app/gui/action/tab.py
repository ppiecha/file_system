from enum import Enum
from functools import partial
from typing import Callable

from PySide6.QtCore import Qt
from PySide6.QtGui import QKeySequence
from PySide6.QtWidgets import QWidget

from src.app.gui.action.command import Action


class TabAction(str, Enum):
    NEW = "New"
    CLOSE_ALL = "Close all tabs"
    CLOSE_OTHER = "Close other tabs"
    CLOSE = "Close"


def create_new_tab_action(parent: QWidget) -> Action:
    return Action(
        parent=parent,
        caption=TabAction.NEW.value,
        shortcut=QKeySequence(Qt.CTRL | Qt.Key_T),
        slot=partial(parent.open_root_page, find_existing=True),
    )


def create_close_all_tabs_action(parent_func: Callable) -> Action:
    return Action(
        parent=parent_func().main_form,
        caption=TabAction.CLOSE_ALL.value,
        shortcut=QKeySequence(Qt.CTRL | Qt.Key_F4),
        slot=lambda: parent_func().close_all_pages(),
    )


def create_close_tab_action(parent_func: Callable, index_func: Callable) -> Action:
    return Action(
        parent=parent_func().main_form,
        caption=TabAction.CLOSE.value,
        shortcut=QKeySequence(Qt.SHIFT | Qt.CTRL | Qt.Key_T),
        slot=lambda: parent_func().close_page(index_func=index_func),
    )
