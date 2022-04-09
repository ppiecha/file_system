import os.path
from typing import List, Callable, Tuple, Optional

from PySide2.QtCore import QDir, QFileInfo, QMimeData, QUrl, Qt
from PySide2.QtWidgets import QMessageBox, QApplication

from src.app.utils.constant import APP_NAME
from src.app.utils.logger import get_console_logger
from src.app.utils.shell import paste, copy_file, copy, delete_file, cut, delete
from src.app.utils.thread import run_in_thread

logger = get_console_logger(name=__name__)
PathList = List[str]


def is_single(paths: PathList) -> bool:
    return len(paths) == 1


def has_common_parent(paths: PathList) -> bool:
    pass


def all_folders(paths: PathList) -> bool:
    return all((QFileInfo(path).isDir() for path in paths))


def all_files(paths: PathList) -> bool:
    return all((QFileInfo(path).isFile() for path in paths))


def extract_path(item: str) -> str:
    if QFileInfo(item).isFile():
        path = item
    else:
        if item.endswith(os.sep):
            path = item
        else:
            path = "".join([item, os.sep])
    return QFileInfo(path).path()
    # info = QFileInfo(path if QFileInfo(path).isFile() else path if path.endswith(os.sep) else "".join([path, os.sep]))


def only_folders(paths: PathList) -> PathList:
    return [extract_path(item=path) for path in paths]


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


def file_name(path: str) -> str:
    file = QFileInfo(path)
    if not file.isFile():
        raise ValueError(f"Specified path {path} is not a file")
    return file.fileName()


def folder_name(path: str) -> str:
    return QDir(path).dirName()


def validate_single_path(parent, paths: List[str]) -> Tuple[bool, Optional[str]]:
    if len(paths) == 0:
        # QMessageBox.information(parent, APP_NAME, "No path selected")
        return False, None
    if len(paths) > 1:
        QMessageBox.information(parent, APP_NAME, "More than one path selected")
        return False, None
    return True, paths[0]


def cut_items_to_clipboard(parent, path_func: Callable) -> bool:
    is_ok, path = validate_single_path(parent=parent, paths=path_func())
    path = extract_path(item=path)
    if is_ok:
        run_in_thread(parent=parent, target=cut, args=[path], lst=parent.threads)
        return True
    return True


def copy_items_to_clipboard(parent, path_func: Callable) -> bool:
    clipboard = QApplication.clipboard()
    data = QMimeData()
    urls = [QUrl.fromLocalFile(path) for path in path_func()]
    logger.debug(f"Clip copied files {urls}")
    data.setUrls(urls)
    clipboard.setMimeData(data)
    return True


def paste_items_from_clipboard(parent, path_func: Callable) -> bool:
    is_ok, path = validate_single_path(parent=parent, paths=path_func())
    path = extract_path(item=path)
    if is_ok:
        run_in_thread(parent=parent, target=paste, args=[path], lst=parent.threads)
        return True
    return False


def delete_items(parent, path_func: Callable) -> bool:
    paths = path_func()
    modifiers = QApplication.keyboardModifiers()
    run_in_thread(parent=parent, target=delete, args=[paths, modifiers == Qt.ControlModifier], lst=parent.threads)
    return True


def rename_item(parent, path_func: Callable) -> bool:
    pass


def duplicate_item(source_path: str, target_path):
    pass

