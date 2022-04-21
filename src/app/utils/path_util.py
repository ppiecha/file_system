import os.path
import subprocess
from typing import List, Callable, Tuple, Optional

from PySide2.QtCore import QDir, QFileInfo, QMimeData, QUrl, Qt
from PySide2.QtWidgets import QMessageBox, QApplication, QInputDialog

from src.app.gui.dialog.sys_path_edit import SysPathDialog
from src.app.utils.constant import APP_NAME
from src.app.utils.logger import get_console_logger
from src.app.utils.shell import paste, cut, delete, rename, copy, copy_file
from src.app.utils.thread import run_in_thread

logger = get_console_logger(name=__name__)
Paths = List[str]


def is_single(paths: Paths) -> bool:
    return len(paths) == 1


def has_common_parent(paths: Paths) -> bool:
    pass


def all_folders(paths: Paths) -> bool:
    return all((QFileInfo(path).isDir() for path in paths))


def all_files(paths: Paths) -> bool:
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


def only_folders(paths: Paths) -> Paths:
    return [extract_path(item=path) for path in paths]


def only_files(paths: Paths) -> Paths:
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


def join(items: List[str]) -> str:
    return "/".join(items)


def quote_path(text: str) -> str:
    if QFileInfo(text).exists():
        return f'"{text}"'
    return text


def validate_single_path(parent, paths: List[str]) -> Tuple[bool, Optional[str]]:
    if len(paths) == 0:
        # QMessageBox.information(parent, APP_NAME, "No path selected")
        return False, None
    if len(paths) > 1:
        QMessageBox.information(parent, APP_NAME, "More than one path selected")
        return False, None
    return True, paths[0]


def rename_if_exists(parent, path: str, user_is_aware: bool = False) -> Optional[str]:
    item = QFileInfo(path)
    item_name = file_name(path=path) if item.isFile() else folder_name(path=path)
    parent_item_path = parent_path(path=path)
    item_type_name = "File" if item.isFile() else "Folder"
    while item.exists():
        resp = QMessageBox.Yes
        if not user_is_aware:
            resp = QMessageBox.question(
                parent,
                APP_NAME,
                f"{item_type_name} <b> {item_name} </b> already exists in {parent_item_path} <br> Use another name?",
            )
        print(resp)
        if resp == QMessageBox.Yes:
            label = f"New {item_type_name} name"
            name, ok = QInputDialog.getText(parent, label, label, text=item_name)
            if ok:
                if name:
                    new_path = os.path.join(parent_item_path, name)
                    if not QFileInfo(new_path).exists():
                        return new_path
                else:
                    QMessageBox.information(parent, APP_NAME, "Name cannot be empty")
            else:
                return None
        else:
            return path
    return path


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
    is_ok, path = validate_single_path(parent=parent, paths=path_func())
    if is_ok:
        new_path = rename_if_exists(parent=parent, path=path, user_is_aware=True)
        if not new_path:
            return False
        run_in_thread(parent=parent, target=rename, args=[path, new_path, False], lst=parent.threads)
    return True


def duplicate_item(parent, path_func: Callable) -> bool:
    is_ok, path = validate_single_path(parent=parent, paths=path_func())
    if is_ok:
        new_path = rename_if_exists(parent=parent, path=path, user_is_aware=True)
        if not new_path:
            return False
        info = QFileInfo(path)
        if info.isFile():
            run_in_thread(parent=parent, target=copy_file, args=[path, new_path, False], lst=parent.threads)
        else:
            run_in_thread(
                parent=parent,
                target=copy,
                args=[os.path.join(path, "*.*"), new_path, False],
                lst=parent.threads,
            )
    return True


# pylint: disable=consider-using-with
def exec_item(sys_path: str, args: List[str]):
    sys_path = quote_path(text=sys_path)
    args = [quote_path(text=arg) for arg in args]
    cmd = [sys_path] + args
    cmd = " ".join(cmd)
    logger.debug(f"cmd {cmd}")
    subprocess.Popen(cmd)


def view_item(parent, path_func: Callable) -> bool:
    if not parent.app.sys_paths.vs_code.path:
        SysPathDialog.exec(parent=parent, sys_paths=parent.app.sys_paths.vs_code.path)
    if parent.app.sys_paths.vs_code.path:
        exec_item(sys_path=parent.app.sys_paths.vs_code.path, args=["-n"] + path_func())
        return True
    return False
