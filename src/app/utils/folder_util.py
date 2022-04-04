import os
from typing import Callable

from PySide2.QtCore import QDir
from PySide2.QtWidgets import QInputDialog, QMessageBox

from src.app.utils.path_util import validate_single_path, logger
from src.app.utils.constant import APP_NAME


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
