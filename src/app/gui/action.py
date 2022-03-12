import subprocess
from functools import partial
from typing import Callable, List

from PySide2.QtCore import Qt
from PySide2.QtGui import QIcon, QKeySequence
from PySide2.QtWidgets import QAction, QMenu, QWidget

from src.app.model.path import create_folder, create_file
from src.app.utils.shell import start_file, open_folder


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


def create_folder_action(parent: QWidget, path: str, shortcut: bool = False) -> Action:
    return Action(
        parent=parent,
        caption="Create new folder",
        shortcut=QKeySequence(Qt.Key_F7) if shortcut else None,
        slot=partial(create_folder, parent, path),
        tip="Creates sub-folder under current folder",
    )


def create_file_action(parent: QWidget, path: str, shortcut: bool = False) -> Action:
    return Action(
        parent=parent,
        caption="Create new file",
        shortcut=QKeySequence(Qt.Key_F9) if shortcut else None,
        slot=partial(create_file, parent, path),
        tip="Creates new file under current folder",
    )


def create_pin_action(parent: QWidget, path: str, pin: bool = True) -> Action:
    return Action(
        parent=parent,
        caption="Pin" if pin else "Unpin",
        shortcut=None,
        slot=partial(parent.pin, path, pin),
        tip="Pins tree to current folder" if pin else "Unpins tree",
    )


def open_file_action(parent: QWidget, paths: List[str]) -> Action:
    def open_paths():
        for path in paths:
            start_file(file_name=path)

    return Action(
        parent=parent,
        caption="Open",
        shortcut=None,
        slot=open_paths,
        tip="Opens selected file",
    )


def open_folder_action(parent: QWidget, paths: List[str]) -> Action:
    def open_paths():
        for path in paths:
            open_folder(dir_name=path)

    return Action(
        parent=parent,
        caption="Open",
        shortcut=None,
        slot=open_paths,
        tip="Opens selected folder",
    )


def open_console_action(parent: QWidget, path: str) -> Action:
    return Action(
        parent=parent,
        caption="Open console",
        shortcut=None,
        slot=lambda: subprocess.Popen(["start", "cmd", "/k", f"cd {path} & deactivate"], shell=True),
        tip=f"Open console in {path}",
    )
