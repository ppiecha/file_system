import os.path
from typing import List, Callable, Tuple, Optional

from PySide2.QtCore import QDir, QFileInfo
from PySide2.QtWidgets import QMessageBox, QInputDialog

from src.app.utils.constant import APP_NAME
from src.app.utils.logger import get_console_logger
from src.app.utils.shell import new_file

logger = get_console_logger(name=__name__)
PathList = List[str]


def is_single(paths: PathList) -> bool:
    return len(paths) == 1


def has_common_parent(paths: PathList) -> bool:
    pass


def all_folders(paths: PathList) -> bool:
    return all((QFileInfo(path).isDir() for path in paths))


def only_folders(paths: PathList) -> PathList:
    return [path for path in paths if QFileInfo(path).isDir()]


def all_files(paths: PathList) -> bool:
    return all((QFileInfo(path).isFile() for path in paths))


def only_files(paths: PathList) -> PathList:
    return [path for path in paths if QFileInfo(path).isFile()]


def parent_path(path: str):
    if not path:
        return None
    logger.info(f"parent path {path}")
    directory = QDir(path)
    directory.cdUp()
    logger.info(f"parent path {directory.path()}")
    return directory.path()


def path_caption(path: str) -> str:
    directory = QDir(path)
    if directory.isRoot():
        return path.lower()
    # logger.debug(f"path_caption '{directory.dirName()}'")
    return directory.dirName() if directory.dirName() != "." else "/"


def validate_single_path(parent, paths: List[str]) -> Tuple[bool, Optional[str]]:
    if len(paths) == 0:
        QMessageBox.information(parent, APP_NAME, "No path selected")
        return False, None
    if len(paths) > 1:
        QMessageBox.information(parent, APP_NAME, "More than one path selected")
        return False, None
    return True, paths[0]


def create_folder(parent, path_func: Callable) -> bool:
    is_ok, path = validate_single_path(parent=parent, paths=path_func())
    if not is_ok:
        return False
    label = "New folder name"
    names, ok = QInputDialog.getText(parent, label, label, text=QDir(path).dirName())
    if ok and names:
        for name in names.split(";"):
            directory = QDir(os.path.join(path, name))
            logger.info(f"new folder {directory.absolutePath()}")
            if directory.exists():
                QMessageBox.information(parent, APP_NAME, f"Folder {path} already exists")
            else:
                directory.mkpath(directory.absolutePath())
        return True
    return False


def create_file(parent, path_func: Callable) -> bool:
    is_ok, path = validate_single_path(parent=parent, paths=path_func())
    logger.debug(f"single path {path}")
    if not is_ok:
        return False
    label = "New file name"
    info = QFileInfo(path if QFileInfo(path).isFile() else path if path.endswith(os.sep) else "".join([path, os.sep]))
    logger.debug(f"info {info.path()}")
    text = QFileInfo(path).fileName() if QFileInfo(path).isFile() else "new.sql"
    names, ok = QInputDialog.getText(parent, label, label, text=text)
    if ok and names:
        for name in names.split(";"):
            file = QFileInfo(os.path.join(info.path(), name))
            logger.info(f"new file {file.absoluteFilePath()}")
            if file.exists():
                QMessageBox.information(parent, APP_NAME, f"File {name} already exists in {path}")
            else:
                new_file(file.absoluteFilePath())
        return True
    return False