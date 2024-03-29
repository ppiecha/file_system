import subprocess
from enum import Enum
from functools import partial
from typing import Callable

from PySide6.QtCore import Qt
from PySide6.QtGui import QKeySequence

import src.app.utils.folder_util
from src.app.gui.action.command import Action
from src.app.utils import path_util
from src.app.utils.shell import open_folder


class FolderAction(Enum):
    SELECT = "Open in current tab"
    SELECT_IN_NEW_TAB = "Open in new tab"
    PIN = "Pin"
    UNPIN = "Unpin"
    CREATE = "Create folder"
    OPEN_EXT = "Open (externally)"
    OPEN_TAB = "Open (new tab)"
    OPEN_WIN = "Open (new window)"
    OPEN_VS = "Open (VS Code)"
    OPEN_CONSOLE = "Open (console)"


def create_folder_action(parent_func: Callable, path_func: Callable) -> Action:
    return Action(
        parent=parent_func().main_form,
        caption=FolderAction.CREATE.value,
        shortcut=QKeySequence(Qt.CTRL | Qt.SHIFT | Qt.Key_N),
        slot=partial(src.app.utils.folder_util.create_folder, parent_func, path_func),
        tip="Creates sub-folder under current folder",
    )


def create_select_folder_action(parent_func: Callable) -> Action:
    return Action(
        parent=parent_func().main_form,
        caption=FolderAction.SELECT.value,
        shortcut=QKeySequence(Qt.CTRL | Qt.Key_O),
        slot=lambda: parent_func().select_folder(),
        tip="Open folder in current tab",
    )


def create_select_folder_in_new_tab_action(parent_func: Callable) -> Action:
    return Action(
        parent=parent_func().main_form,
        caption=FolderAction.SELECT_IN_NEW_TAB.value,
        shortcut=QKeySequence(Qt.CTRL | Qt.SHIFT | Qt.Key_O),
        slot=lambda: parent_func().tree_box.open_user_defined_page(),
        tip="Open folder in new tab",
    )


def create_pin_action(parent_func: Callable, path_func: Callable, pin: bool = True) -> Action:
    return Action(
        parent=parent_func().main_form,
        caption=FolderAction.PIN.value if pin else FolderAction.UNPIN.value,
        shortcut=None,
        slot=lambda: parent_func().pin(path_func=path_func, pin=pin),
        tip="Pins tree to current folder" if pin else "Unpins tree",
    )


def create_open_folder_externally_action(parent_func: Callable, path_func: Callable) -> Action:
    def open_paths():
        for path in path_util.extract_folders(paths=path_func()):
            open_folder(dir_name=path)

    return Action(
        parent=parent_func().main_form,
        caption=FolderAction.OPEN_EXT.value,
        shortcut=QKeySequence(Qt.CTRL | Qt.SHIFT | Qt.Key_Return),
        slot=open_paths,
        tip="Opens selected folder in external browser",
    )


def create_open_folder_in_new_tab_action(parent_func: Callable, path_func: Callable) -> Action:
    def open_paths():
        for path in path_util.extract_folders(paths=path_func()):
            parent_func().tree_box.open_tree_page(pinned_path=path, find_existing=True, go_to_page=True)

    return Action(
        parent=parent_func().main_form,
        caption=FolderAction.OPEN_TAB.value,
        shortcut=QKeySequence(Qt.CTRL | Qt.Key_M),
        slot=open_paths,
        tip="Opens selected folders in new tabs",
    )


# pylint: disable=consider-using-with
def create_open_console_action(parent_func: Callable, path_func: Callable) -> Action:
    def open_paths():
        for path in path_util.extract_folders(paths=path_func()):
            subprocess.Popen(["start", "cmd", "/k", f"cd {path} & deactivate"], shell=True)

    return Action(
        parent=parent_func().main_form,
        caption=FolderAction.OPEN_CONSOLE.value,
        shortcut=QKeySequence(Qt.CTRL | Qt.Key_P),
        slot=open_paths,
        tip="Open console in selected locations",
    )
