import os
from typing import Callable

from PySide6.QtCore import QDir
from PySide6.QtWidgets import QInputDialog, QMessageBox

from src.app.utils.path_util import validate_single_path, logger, rename_if_exists
from src.app.utils.constant import APP_NAME


def create_folder(parent_func: Callable, path_func: Callable) -> bool:
    parent = parent_func()
    is_ok, path = validate_single_path(parent=parent, paths=path_func())
    if not is_ok:
        return False
    label = "New folder name"
    names, ok = QInputDialog.getText(parent, label, label, text=QDir(path).dirName())
    if ok and names:
        for name in names.split(";"):
            new_dir_path = os.path.join(path, name)
            dir_path = rename_if_exists(parent=parent, path=new_dir_path)
            if not dir_path:
                return False
            directory = QDir(dir_path)
            logger.info(f"new folder {directory.absolutePath()}")
            if directory.exists():
                if dir_path != new_dir_path:
                    QMessageBox.information(parent, APP_NAME, f"Folder {name} already exists in path {path}")
            else:
                directory.mkpath(directory.absolutePath())
                parent.set_selection([directory.absolutePath()])
        return True
    return False
