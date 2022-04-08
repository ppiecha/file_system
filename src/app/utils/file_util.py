import os
from typing import Callable

from PySide2.QtCore import QFileInfo
from PySide2.QtWidgets import QMessageBox, QInputDialog, QApplication

from src.app.utils.path_util import logger, validate_single_path, extract_path
from src.app.utils.constant import APP_NAME
from src.app.utils.shell import new_file


def create_text_file(parent, file_name: str, text: str = None) -> bool:
    with open(file=file_name, mode="w", encoding="UTF-8") as file:
        try:
            file.write(text)
            return True
        except Exception as e:
            logger.error(str(e))
            QMessageBox.information(parent, APP_NAME, str(e))
            return False


def create_file(parent, path_func: Callable, text: str = None) -> bool:
    is_ok, path = validate_single_path(parent=parent, paths=path_func())
    logger.debug(f"single path {path}")
    if not is_ok:
        return False
    label = "New file name"
    # info = QFileInfo(path if QFileInfo(path).isFile() else path if path.endswith(os.sep) else "".join([path, os.sep]))
    path = extract_path(item=path)
    input_text = QFileInfo(path).fileName() if QFileInfo(path).isFile() else "new.sql"
    names, ok = QInputDialog.getText(parent, label, label, text=input_text)
    if ok and names:
        for name in names.split(";"):
            file = QFileInfo(os.path.join(path, name))
            logger.info(f"new file {file.absoluteFilePath()}")
            if file.exists():
                QMessageBox.information(parent, APP_NAME, f"File {name} already exists in {path}")
                return False
            file_name = file.absoluteFilePath()
            if text:
                return create_text_file(parent=parent, file_name=file_name, text=text)
            new_file(file_name=file_name)
        return True
    return False


def create_text_file_from_clip(parent, path_func: Callable) -> bool:
    clipboard = QApplication.clipboard()
    # mime_data = clipboard.mimeData()
    # mime_data.hasText()
    # mime_data.text()
    text = clipboard.text()
    if text:
        return create_file(parent=parent, path_func=path_func, text=text)
    QMessageBox.information(parent, APP_NAME, "Clipboard is empty")
    return False
