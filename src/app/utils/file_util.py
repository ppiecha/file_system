import os
from typing import Callable

from PySide2.QtCore import QFileInfo, QDir
from PySide2.QtWidgets import QMessageBox, QInputDialog, QApplication

from src.app.utils.path_util import logger, validate_single_path, extract_path, rename_if_exists
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
    is_ok, org_path = validate_single_path(parent=parent, paths=path_func())
    logger.debug(f"single path {org_path}")
    if not is_ok:
        return False
    label = "New file name"
    path = extract_path(item=org_path)
    input_text = QFileInfo(org_path).fileName() if QFileInfo(org_path).suffix() else "new.sql"
    names, ok = QInputDialog.getText(parent, label, label, text=input_text)
    if ok and names:
        for name in names.split(";"):
            new_file_path = os.path.join(path, name)
            file_path = rename_if_exists(parent=parent, path=new_file_path)
            if not file_path:
                return False
            file = QFileInfo(file_path)
            logger.info(f"new file {file.absoluteFilePath()}")
            if file.exists():
                if file_path != new_file_path:
                    QMessageBox.information(parent, APP_NAME, f"File {name} already exists in {path}")
                return False
            file_name = file.absoluteFilePath()
            folder_path = extract_path(item=file_name)
            logger.debug(f"folder path {folder_path}")
            folder = QDir(folder_path)
            if not folder.exists():
                folder.mkpath(folder_path)
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
