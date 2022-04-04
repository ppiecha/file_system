from enum import Enum
from typing import Callable

from PySide2.QtCore import Qt
from PySide2.QtGui import QKeySequence
from PySide2.QtWidgets import QWidget

from src.app.gui.action.common import Action


class TabAction(Enum):
    NEW = "New"
    CLOSE = "Close"


def create_new_tab_action(parent: QWidget) -> Action:
    return Action(
        parent=parent,
        caption=TabAction.NEW.value,
        shortcut=QKeySequence(Qt.CTRL + Qt.Key_N),
        slot=parent.open_root_page,
    )


def create_close_tab_action(parent_func: Callable, index_func: Callable) -> Action:
    return Action(
        parent=parent_func().main_form,
        caption=TabAction.CLOSE.value,
        shortcut=QKeySequence(Qt.SHIFT + Qt.CTRL + Qt.Key_T),
        slot=lambda: parent_func().close_page(index_func=index_func),
    )
