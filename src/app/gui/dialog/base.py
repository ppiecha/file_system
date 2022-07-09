import logging
from typing import Callable, Dict, Any

from PySide2.QtCore import QDir
from PySide2.QtGui import Qt
from PySide2.QtWidgets import (
    QDialog,
    QFormLayout,
    QLineEdit,
    QDialogButtonBox,
    QFileDialog,
    QAbstractButton,
    QStyle,
    QMessageBox,
    QTextEdit,
    QSizePolicy,
)
from pydantic import BaseModel

from src.app.gui.widget import Layout
from src.app.utils.logger import get_console_logger

logger = get_console_logger(name=__name__, log_level=logging.DEBUG)


def select_folder(parent, text: str = None, caption: str = "Select folder") -> str:
    path = text if text else QDir.homePath()
    return QFileDialog.getExistingDirectory(parent, caption, path)


def select_file(parent, text: str = None) -> str:
    path = text if text else QDir.homePath()
    file_name, _ = QFileDialog.getOpenFileName(parent, "Select file", path, "Executables (*.exe)")
    return file_name


class BaseEdit(QLineEdit):
    def __init__(self, action_delegate: Callable, text: str = None, post_action: Callable = None, parent=None):
        super().__init__(text, parent)
        self.action_delegate = action_delegate
        self.post_action = post_action
        self.main_form = parent
        icon = self.style().standardIcon(QStyle.SP_DirIcon)
        self.action = self.addAction(icon, QLineEdit.TrailingPosition)
        self.action.triggered.connect(self.on_select)

    def on_select(self):
        old_text = self.text()
        text = self.action_delegate(parent=self, text=old_text)
        self.setText(text if text else old_text)
        if self.post_action and text:
            self.post_action(text)


class PathEdit(BaseEdit):
    def __init__(self, text: str = None, post_action: Callable = None, parent=None):
        super().__init__(action_delegate=select_folder, text=text, post_action=post_action, parent=parent)


class FileEdit(BaseEdit):
    def __init__(self, text: str = None, post_action: Callable = None, parent=None):
        super().__init__(action_delegate=select_file, text=text, post_action=post_action, parent=parent)


Properties = Dict[str, Dict[str, Any]]


class FormDialog(QDialog):
    def __init__(self, parent, entity: BaseModel, caption: str):
        super().__init__(parent=parent)
        self.setWindowTitle(caption)
        self.setSizeGripEnabled(True)
        self.layout = Layout()
        self.form = QFormLayout()
        self.form.setContentsMargins(10, 10, 10, 10)
        self.form.setSpacing(5)
        self.entity = entity
        self.properties: Properties = entity.dict()
        self.components = {}
        # logger.debug(f"props {self.properties}")
        self.populate_form(self.properties)
        self.buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel, Qt.Horizontal)
        self.layout.addLayout(self.form)
        self.layout.addWidget(self.buttons)
        self.setLayout(self.layout)
        self.resize(400, self.size().height())
        self.buttons.clicked.connect(self.on_button_clicked)

    def on_button_clicked(self, button: QAbstractButton):
        raise NotImplementedError

    def populate_form(self, properties: Properties):
        raise NotImplementedError

    def validate_input(self) -> bool:
        raise NotImplementedError

    def get_entity(self) -> BaseModel:
        raise NotImplementedError


class CustomMessageBox(QMessageBox):
    def __init__(self, *args, **kvargs):
        QMessageBox.__init__(self, *args, **kvargs)
        self.setSizeGripEnabled(True)

    def event(self, e):
        result = QMessageBox.event(self, e)

        self.setMinimumHeight(0)
        self.setMaximumHeight(16777215)
        self.setMinimumWidth(0)
        self.setMaximumWidth(16777215)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        text_edit = self.findChild(QTextEdit)
        if text_edit is not None:
            text_edit.setMinimumHeight(0)
            text_edit.setMaximumHeight(16777215)
            text_edit.setMinimumWidth(0)
            text_edit.setMaximumWidth(16777215)
            text_edit.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        return result
