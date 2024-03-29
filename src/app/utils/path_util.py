from __future__ import annotations
import math
import os.path
import subprocess
import logging
import typing
from typing import List, Callable, Tuple, Optional, Dict

from PySide6.QtCore import QDir, QFileInfo, QMimeData, QUrl, Qt, QDirIterator
from PySide6.QtWidgets import QMessageBox, QApplication, QInputDialog

from src.app.gui.dialog.base import select_folder
from src.app.gui.dialog.sys_path_edit import SysPathDialog


from src.app.utils.constant import APP_NAME, Context, DEFAULT_ENCODING
from src.app.utils.logger import get_console_logger
from src.app.utils.shell import paste, cut, delete, rename, copy, copy_file, fail, move
from src.app.utils.thread import run_in_thread

if typing.TYPE_CHECKING:
    from src.app.model.search import LineHit


logger = get_console_logger(name=__name__, log_level=logging.ERROR)
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
    info = QFileInfo(item)
    path = item
    if info.isDir():
        if path[-1] not in ("\\", "/"):
            path = "".join([item, "/"])
    return QFileInfo(path).path()


def extract_folders(paths: Paths) -> Paths:
    return [extract_path(item=path) for path in paths]


def only_folders(paths: Paths) -> Paths:
    return [path for path in paths if QFileInfo(path).isDir()]


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
    if path is None:
        return "/"
    directory = QDir(path)
    if directory.isRoot():
        return path.lower()
    # logger.debug(f"path_caption '{directory.dirName()}'")
    return directory.dirName() if directory.dirName() != "." else "/"


def file_name(path: str) -> str:
    file = QFileInfo(path)
    if not file.suffix():
        raise ValueError(f"Specified path {path} is not a file")
    return file.fileName()


def file_first_lines(file_path: str, count: int) -> List[str]:
    info = QFileInfo(file_path)
    parts = []
    if not info.isFile():
        fail(f"{file_path} is not a file")
    with open(info.absoluteFilePath(), "r", encoding=DEFAULT_ENCODING) as file:
        for line_no, line in enumerate(file):
            parts.append(line.rstrip())
            if line_no >= count:
                break
    return parts


def dir_list(path: str) -> List[str]:
    info = QFileInfo(path)
    parts = []
    if not info.isDir():
        fail(f"{path} is not a directory")
    it = QDirIterator(path)
    while it.hasNext():
        full_path = it.next()
        if it.fileName() not in (".", ".."):
            parts.append(full_path)
    return parts


def convert_size(size_bytes: int):
    if size_bytes == 0:
        return "0B"
    size_name = ("B", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB")
    i = int(math.floor(math.log(size_bytes, 1024)))
    p = math.pow(1024, i)
    s = round(size_bytes / p, 2)
    return f"{str(s)} {str(size_name[i])}"


def folder_name(path: str) -> str:
    return QDir(path).dirName()


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
    if not paths[0]:
        QMessageBox.information(parent, APP_NAME, "Empty path selected")
        return False, None
    return True, paths[0]


def rename_if_exists(parent, path: str, user_is_aware: bool = False) -> Optional[str]:
    item = QFileInfo(path)
    item_name = file_name(path=path) if item.suffix() else folder_name(path=path)
    parent_item_path = parent_path(path=path)
    item_type_name = "File" if item.suffix() else "Folder"
    while item.exists():
        resp = QMessageBox.Yes
        if not user_is_aware:
            resp = QMessageBox.question(
                parent,
                APP_NAME,
                f"{item_type_name} <b> {item_name} </b> already exists in {parent_item_path} <br> Use another name?",
            )
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
    if is_ok:
        run_in_thread(parent=parent, target=cut, args=[path], threads=parent.threads)
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
    if is_ok:
        path = extract_path(item=path)
        run_in_thread(parent=parent, target=paste, args=[path], threads=parent.threads)
        return True
    return False


def delete_items(parent, path_func: Callable) -> bool:
    paths = path_func()
    modifiers = QApplication.keyboardModifiers()
    run_in_thread(parent=parent, target=delete, args=[paths, modifiers == Qt.ControlModifier], threads=parent.threads)
    return True


def rename_item(parent, path_func: Callable) -> bool:
    is_ok, path = validate_single_path(parent=parent, paths=path_func())
    if is_ok:
        new_path = rename_if_exists(parent=parent, path=path, user_is_aware=True)
        if not new_path:
            return False
        run_in_thread(parent=parent, target=rename, args=[path, new_path, False], threads=parent.threads)
    return True


def duplicate_item(parent, path_func: Callable) -> bool:
    is_ok, path = validate_single_path(parent=parent, paths=path_func())
    if is_ok:
        new_path = rename_if_exists(parent=parent, path=path, user_is_aware=True)
        if not new_path:
            return False
        info = QFileInfo(path)
        if info.suffix():
            run_in_thread(parent=parent, target=copy_file, args=[path, new_path, False], threads=parent.threads)
        else:
            run_in_thread(
                parent=parent,
                target=copy,
                args=[os.path.join(path, "*.*"), new_path, False],
                threads=parent.threads,
            )
        return True
    return False


def copy_move(parent, path_func: Callable, move_flag: bool = True) -> bool:
    paths = path_func()
    path = extract_path(paths[0])
    action = "Move" if move_flag else "Copy"
    caption = action + " to location"
    path = select_folder(parent=parent, text=path, caption=caption)
    if path:
        func = move if move_flag else copy
        run_in_thread(
            parent=parent,
            target=func,
            args=[paths, path, False],
            threads=parent.threads,
        )


def run_command(args: List[str]) -> str:
    logger.debug(f"cmd {args}")
    # return subprocess.run(args, stdout=subprocess.PIPE).stdout.decode('utf-8')
    # return subprocess.check_output(args)
    #     capture_output=True, shell=True
    return subprocess.run(args, capture_output=True, shell=True).stdout.decode("utf-8")


def get_repo_url(path: str) -> Optional[str]:
    args = f"cd {path} & git config --get remote.origin.url".split()
    resp = run_command(args=args)
    logger.debug(f"{path} repo url {resp}")
    return resp if resp else None


# pylint: disable=consider-using-with
def exec_item(sys_path: str, args: List[str]):
    path = QFileInfo(sys_path)
    valid_path = path.exists() and path.isFile() and path.isExecutable()
    if not valid_path:
        raise RuntimeError(f"Invalid path {sys_path}. It is not existing executable file")
    sys_path = quote_path(text=sys_path)
    args = [quote_path(text=arg) for arg in args]
    cmd = [sys_path] + args
    cmd = " ".join(cmd)
    logger.debug(f"cmd {cmd}")
    subprocess.Popen(cmd)


def open_in_chrome(parent, urls: List[str]) -> bool:
    if not parent.app.sys_paths.chrome.path:
        SysPathDialog.exec(parent=parent, sys_paths=parent.app.sys_paths)
    if parent.app.sys_paths.chrome.path:
        exec_item(sys_path=parent.app.sys_paths.chrome.path, args=urls)
        return True
    return False


def go_to_repo(parent, path_func: Callable) -> bool:
    is_ok, path = validate_single_path(parent=parent, paths=path_func())
    if is_ok:
        path = extract_path(item=path)
        url = get_repo_url(path=path)
        if url:
            open_in_chrome(parent=parent, urls=[url])
            return True
    return False


def view_item(parent, path_func: Callable, line_func: Callable[[], Dict[str, LineHit]] | None = None) -> bool:
    if not parent.app.sys_paths.vs_code.path:
        SysPathDialog.exec(parent=parent, sys_paths=parent.app.sys_paths)
    paths = path_func()
    if line_func:
        path_hits = line_func()
        for path in paths:
            if path in path_hits:
                line_hit = path_hits[path]
                cmd = path
                if line_hit.line_number is not None:
                    cmd = f"{cmd}:{str(line_hit.line_number)}"
                    if line_hit.column_number() is not None:
                        cmd = f"{cmd}:{str(line_hit.column_number())}"
                args = ["-g"] + [cmd]
            else:
                args = [path]
            exec_item(sys_path=parent.app.sys_paths.vs_code.path, args=args)
        return True
    if paths and parent.app.sys_paths.vs_code.path:
        files = only_files(paths=paths)
        if paths != files:
            paths = ["-n"] + paths
        exec_item(sys_path=parent.app.sys_paths.vs_code.path, args=paths)
        return True
    return False


# pylint: disable=too-many-nested-blocks
def edit_item(parent, path_func: Callable, line_func: Callable[[], Dict[str, LineHit]] | None = None) -> bool:
    if not parent.app.sys_paths.notepad.path or not parent.app.sys_paths.vs_code.path:
        logger.info(f"sys paths before edit {parent.app.sys_paths}")
        SysPathDialog.exec(parent=parent, sys_paths=parent.app.sys_paths)
    paths = path_func()
    folders = only_folders(paths=paths)
    files = only_files(paths=paths)
    logger.debug(f"folders {folders} files {files}")
    if parent.app.sys_paths.vs_code.path and parent.app.sys_paths.notepad.path:
        if folders:
            exec_item(sys_path=parent.app.sys_paths.vs_code.path, args=["-n"] + folders)
        if files:
            path_hits = line_func()
            for file in files:
                if file in path_hits:
                    line_hit = path_hits[file]
                    cmd = file
                    if line_hit.line_number is not None:
                        cmd = f"-n{str(line_hit.line_number)} {cmd}"
                        if line_hit.column_number() is not None:
                            cmd = f"-c{str(line_hit.column_number())} {cmd}"
                    args = [cmd]
                else:
                    args = [file]
                exec_item(sys_path=parent.app.sys_paths.notepad.path, args=args)
        return True
    return False


def go_to_item(parent, path_func: Callable, context_func: Callable) -> bool:
    if context_func() == Context.search:
        paths, is_ok = path_func(), True
    else:
        paths = path_func(show_info=False)
        path = paths[0] if paths else ""
        path, is_ok = QInputDialog.getText(parent, "Go to item", "Specify file or folder", text=path)
        paths = [path]
    if is_ok:
        for path in paths:
            info = QFileInfo(path)
            folder = extract_path(item=path)
            selection = None
            if not info.exists():
                QMessageBox.information(parent, APP_NAME, "Specified file or folder doesn't exist")
                return False
            if info.isFile():
                selection = [path]
            if Qt.ControlModifier in QApplication.keyboardModifiers():
                parent.current_group_panel().tree_box.open_tree_page(
                    pinned_path=folder, find_existing=True, go_to_page=True, selection=selection
                )
            else:
                parent.current_tree().pinned_path = folder
                parent.current_tree().set_selection(selection=selection)
                parent.current_tree().set_last_selected_path(path=selection[0] if selection else None)
            parent.activate()
    return False


def search_in_path(parent, path_func: Callable):
    if paths := path_func():
        parent.search_dlg.show()
        for path in extract_folders(paths=paths):
            parent.search_dlg.search_control.add_search_panel(path=path)
