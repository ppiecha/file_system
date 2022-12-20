import logging
from enum import Enum
from typing import Callable

from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon, QKeySequence, QAction
from PySide6.QtWidgets import QMenu, QWidget

from src.app.utils.path_util import (
    copy_items_to_clipboard,
    paste_items_from_clipboard,
    cut_items_to_clipboard,
    delete_items,
    rename_item,
    duplicate_item,
    view_item,
    go_to_item,
    go_to_repo,
    edit_item,
    validate_single_path,
    copy_move,
    search_in_path,
)
from src.app.utils.logger import get_console_logger
from src.app.utils.shell import properties

logger = get_console_logger(name=__name__, log_level=logging.ERROR)


class CommonAction(str, Enum):
    GO_TO = "Go to..."
    GO_TO_REPO = "Go to Git repository"
    CUT = "Cut"
    COPY = "Copy"
    COPY_TO = "Copy to..."
    MOVE_TO = "Move to..."
    PASTE = "Paste"
    DELETE = "Delete"
    RENAME = "Rename"
    VIEW = "View"
    EDIT = "Edit"
    DUPLICATE = "Duplicate"
    PROPERTIES = "Properties..."
    COMPARE = "Compare/Diff"
    SEARCH = "Search..."


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
            # logger.debug(f"shortcut list {list(map(lambda s: s.toString(), shortcut))}")
            self.setShortcuts(shortcut)
        elif shortcut is not None:
            self.setShortcut(shortcut)
        self.setToolTip(tip or caption)
        self.setStatusTip(status_tip or caption)
        if slot:
            self.triggered.connect(slot)
        # self.setShortcutContext(Qt.ApplicationShortcut)


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
        shortcut=Qt.CTRL | Qt.Key_X,
        slot=lambda: cut_items_to_clipboard(parent=parent_func().main_form, path_func=path_func),
        tip="Cut item to clipboard",
    )


def create_copy_items_to_clipboard_action(parent_func: Callable, path_func: Callable) -> Action:
    return Action(
        parent=parent_func().main_form,
        caption=CommonAction.COPY.value,
        shortcut=Qt.CTRL | Qt.Key_C,
        slot=lambda: copy_items_to_clipboard(parent=parent_func(), path_func=path_func),
        tip="Copies selected items to clipboard",
    )


def create_paste_items_from_clipboard_action(parent_func: Callable, path_func: Callable) -> Action:
    return Action(
        parent=parent_func().main_form,
        caption=CommonAction.PASTE.value,
        shortcut=Qt.CTRL | Qt.Key_V,
        slot=lambda: paste_items_from_clipboard(parent=parent_func().main_form, path_func=path_func),
        tip="Paste item from clipboard into selected path",
    )


def create_delete_items_action(parent_func: Callable, path_func: Callable) -> Action:
    return Action(
        parent=parent_func().main_form,
        caption=CommonAction.DELETE.value,
        shortcut=[QKeySequence(Qt.Key_Delete), QKeySequence(Qt.CTRL | Qt.Key_Delete)],
        slot=lambda: delete_items(parent=parent_func().main_form, path_func=path_func),
        tip="Deletes selected items",
    )


def create_rename_action(parent_func: Callable, path_func: Callable) -> Action:
    return Action(
        parent=parent_func().main_form,
        caption=CommonAction.RENAME.value,
        shortcut=QKeySequence(Qt.Key_F2),
        slot=lambda: rename_item(parent=parent_func().main_form, path_func=path_func),
        tip="Renames item",
    )


def create_duplicate_action(parent_func: Callable, path_func: Callable) -> Action:
    return Action(
        parent=parent_func().main_form,
        caption=CommonAction.DUPLICATE.value,
        shortcut=QKeySequence(Qt.Key_F5),
        slot=lambda: duplicate_item(parent=parent_func().main_form, path_func=path_func),
        tip="Duplicate item",
    )


def create_view_action(parent_func: Callable, path_func: Callable, line_func: Callable) -> Action:
    return Action(
        parent=parent_func().main_form,
        caption=CommonAction.VIEW.value,
        shortcut=[QKeySequence(Qt.Key_F3), QKeySequence(Qt.CTRL | Qt.Key_Return)],
        slot=lambda: view_item(parent=parent_func().main_form, path_func=path_func, line_func=line_func),
        tip="View item",
    )


def create_edit_action(parent_func: Callable, path_func: Callable, line_func: Callable) -> Action:
    return Action(
        parent=parent_func().main_form,
        caption=CommonAction.EDIT.value,
        shortcut=QKeySequence(Qt.Key_F4),
        slot=lambda: edit_item(parent=parent_func().main_form, path_func=path_func, line_func=line_func),
        tip="Edit item",
    )


def create_go_to_action(parent_func: Callable, path_func: Callable, context_func: Callable) -> Action:
    return Action(
        parent=parent_func().main_form,
        caption=CommonAction.GO_TO.value,
        shortcut=QKeySequence(Qt.CTRL | Qt.Key_G),
        slot=lambda: go_to_item(parent=parent_func().main_form, path_func=path_func, context_func=context_func),
        tip="Go to specified item",
    )


def create_go_to_repo_action(parent_func: Callable, path_func: Callable) -> Action:
    return Action(
        parent=parent_func().main_form,
        caption=CommonAction.GO_TO_REPO.value,
        shortcut=QKeySequence(Qt.CTRL | Qt.Key_R),
        slot=lambda: go_to_repo(parent=parent_func().main_form, path_func=path_func),
        tip="Go to related Git repository URL",
    )


def create_properties_action(parent_func: Callable, path_func: Callable) -> Action:
    def properties_fun(parent=parent_func().main_form, path_func=path_func):
        is_ok, path = validate_single_path(parent=parent, paths=path_func())
        if is_ok:
            properties(path=path)

    return Action(
        parent=parent_func().main_form,
        caption=CommonAction.PROPERTIES.value,
        shortcut=QKeySequence(Qt.Key_F7),
        slot=lambda: properties_fun(parent=parent_func().main_form, path_func=path_func),
        tip="Show item properties",
    )


def create_copy_to_action(parent_func: Callable, path_func: Callable) -> Action:
    return Action(
        parent=parent_func().main_form,
        caption=CommonAction.COPY_TO.value,
        shortcut=QKeySequence(Qt.CTRL | Qt.Key_F5),
        slot=lambda: copy_move(parent=parent_func().main_form, path_func=path_func, move_flag=False),
        tip="Copy items to selected location",
    )


def create_move_to_action(parent_func: Callable, path_func: Callable) -> Action:
    return Action(
        parent=parent_func().main_form,
        caption=CommonAction.MOVE_TO.value,
        shortcut=QKeySequence(Qt.Key_F6),
        slot=lambda: copy_move(parent=parent_func().main_form, path_func=path_func, move_flag=True),
        tip="Move items to selected location",
    )


def create_search_action(parent_func: Callable, path_func: Callable) -> Action:
    return Action(
        parent=parent_func().main_form,
        caption=CommonAction.SEARCH.value,
        shortcut=QKeySequence(Qt.CTRL | Qt.Key_F),
        slot=lambda: search_in_path(parent=parent_func().main_form, path_func=path_func),
        tip="Search in specified path",
    )
