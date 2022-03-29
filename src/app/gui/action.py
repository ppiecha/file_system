import subprocess
from enum import Enum
from functools import partial
from typing import Callable

from PySide2.QtCore import Qt
from PySide2.QtGui import QIcon, QKeySequence
from PySide2.QtWidgets import QAction, QMenu, QWidget

from src.app.model import path_util
from src.app.utils.logger import get_console_logger
from src.app.utils.shell import start_file, open_folder

logger = get_console_logger(name=__name__)


class FileAction(Enum):
    CREATE = "Create file"
    CREATE_CLIP = "Create from clipboard"
    OPEN = "Open file"
    OPEN_VS = "Open (VS Code)"


class FolderAction(Enum):
    SELECT = "Select"
    PIN = "Pin"
    UNPIN = "Unpin"
    CREATE = "Create folder"
    OPEN_EXT = "Open (externally)"
    OPEN_TAB = "Open (new tab)"
    OPEN_WIN = "Open (new window)"
    OPEN_VS = "Open (VS Code)"
    OPEN_CONSOLE = "Open (console)"


class TabAction(Enum):
    NEW = "New"
    CLOSE = "Close"


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
        if shortcut:
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


def create_folder_action(parent: QWidget, path_func: Callable) -> Action:
    return Action(
        parent=parent,
        caption=FolderAction.CREATE.value,
        shortcut=QKeySequence(Qt.Key_F7),
        slot=partial(path_util.create_folder, parent, path_func),
        tip="Creates sub-folder under current folder",
    )


def create_file_action(parent: QWidget, path_func: Callable) -> Action:
    return Action(
        parent=parent,
        caption=FileAction.CREATE.value,
        shortcut=QKeySequence(Qt.Key_F9),
        slot=partial(path_util.create_file, parent, path_func),
        tip="Creates new file under current folder",
    )


def create_select_folder_action(parent_func: Callable) -> Action:
    return Action(
        parent=parent_func().main_form,
        caption=FolderAction.SELECT.value,
        shortcut=QKeySequence(Qt.CTRL + Qt.Key_D),
        slot=lambda: parent_func().select_folder(),
        tip="Pins tree to selected folder",
    )


def create_pin_action(parent_func: Callable, path_func: Callable, pin: bool = True) -> Action:
    return Action(
        parent=parent_func().main_form,
        caption=FolderAction.PIN.value if pin else FolderAction.UNPIN.value,
        shortcut=None,
        slot=lambda: parent_func().pin(path_func=path_func, pin=pin),
        tip="Pins tree to current folder" if pin else "Unpins tree",
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


def create_open_folder_externally_action(parent_func: Callable, path_func: Callable) -> Action:
    def open_paths():
        for path in path_util.only_folders(paths=path_func()):
            open_folder(dir_name=path)

    return Action(
        parent=parent_func().main_form,
        caption=FolderAction.OPEN_EXT.value,
        shortcut=QKeySequence(Qt.CTRL + Qt.Key_E),
        slot=open_paths,
        tip="Opens selected folder in external browser",
    )


def create_open_folder_in_new_tab_action(parent_func: Callable, path_func: Callable) -> Action:
    def open_paths():
        for path in path_util.only_folders(paths=path_func()):
            parent_func().tree_box.open_tree_page(pinned_path=path, find_existing=False)

    return Action(
        parent=parent_func().main_form,
        caption=FolderAction.OPEN_TAB.value,
        shortcut=QKeySequence(Qt.CTRL + Qt.Key_T),
        slot=open_paths,
        tip="Opens selected folders in new tabs",
    )


# pylint: disable=consider-using-with
def create_open_console_action(parent_func: Callable, path_func: Callable) -> Action:
    def open_paths():
        for path in path_util.only_folders(paths=path_func()):
            subprocess.Popen(["start", "cmd", "/k", f"cd {path} & deactivate"], shell=True)

    return Action(
        parent=parent_func().main_form,
        caption=FolderAction.OPEN_CONSOLE.value,
        shortcut=None,
        slot=open_paths,
        tip="Open console in selected locations",
    )


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
