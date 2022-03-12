import os.path
from typing import List

from PySide2.QtCore import QDir, QFileInfo
from PySide2.QtWidgets import QMessageBox, QInputDialog

from src.app.utils.logger import get_console_logger
from src.app.utils.shell import new_file

logger = get_console_logger(name=__name__)
PathList = List[str]


def is_single(paths: PathList) -> bool:
    return len(paths) == 1


def has_common_parent(paths: PathList) -> bool:
    pass


def all_folders(paths: PathList) -> bool:
    return all([QFileInfo(path).isDir() for path in paths])


def all_files(paths: PathList) -> bool:
    return all([QFileInfo(path).isFile() for path in paths])


def parent_path(path: str):
    logger.info(f"parent path {path}")
    dir = QDir(path)
    dir.cdUp()
    logger.info(f"parent path {dir.path()}")
    return dir.path()


def create_folder(parent, path: str) -> bool:
    label = "New folder name"
    name, ok = QInputDialog.getText(parent, label, label, text=QDir(path).dirName())
    if ok and name:
        dir = QDir(os.path.join(path, name))
        logger.info(f"new folder {dir.absolutePath()}")
        if dir.exists():
            QMessageBox.information(parent, "Title", f"Folder {path} already exists")
            return False
        else:
            return dir.mkpath(dir.absolutePath())


def create_file(parent, path: str) -> bool:
    label = "New file name"
    info = QFileInfo(path)
    text = info.fileName() if info.isFile() else "new.sql"
    name, ok = QInputDialog.getText(parent, label, label, text=text)
    if ok and name:
        file = QFileInfo(os.path.join(info.absolutePath(), name))
        logger.info(f"new file {file.absoluteFilePath()}")
        if file.exists():
            QMessageBox.information(parent, "Title", f"File {name} already exists in {path}")
            return False
        else:
            new_file(file.absoluteFilePath())
            return True
