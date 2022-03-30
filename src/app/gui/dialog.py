from typing import Callable

from PySide2.QtCore import QDir
from PySide2.QtGui import Qt
from PySide2.QtWidgets import (
    QDialog,
    QFormLayout,
    QLineEdit,
    QDialogButtonBox,
    QFileDialog,
    QAbstractButton,
    QApplication,
    QStyle,
)

from src.app.gui.widget import Layout
from src.app.model.favorite import Favorite
from src.app.model.path_util import path_caption


class PathEdit(QLineEdit):
    def __init__(self, text: str = None, post_action: Callable = None, parent=None):
        super().__init__(text, parent)
        self.post_action = post_action
        icon = QApplication.style().standardIcon(QStyle.SP_DirIcon)
        self.action = self.addAction(icon, QLineEdit.TrailingPosition)
        self.action.triggered.connect(self.select_folder)

    def select_folder(self):
        path = self.text() if self.text() else QDir.homePath()
        path = QFileDialog.getExistingDirectory(self, "Select directory", path)
        self.setText(path)
        self.post_action(path)


class FavoriteDlg(QDialog):
    def __init__(self, parent, favorite: Favorite = None):
        super().__init__(parent=parent)
        self.layout = Layout()
        self.favorite = None
        self.form = QFormLayout()
        self.form.setContentsMargins(10, 10, 10, 10)
        self.form.setSpacing(5)
        self.name = QLineEdit(favorite.name if favorite else "")
        self.description = QLineEdit(favorite.description if favorite else "")
        self.path = PathEdit(text=favorite.path if favorite else "", post_action=self.path_post_action)
        self.buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel, Qt.Horizontal)
        self.form.addRow("Name", self.name)
        self.form.addRow("Description", self.description)
        self.form.addRow("Path", self.path)
        self.setSizeGripEnabled(False)
        self.layout.addLayout(self.form)
        self.layout.addWidget(self.buttons)
        self.setLayout(self.layout)

        self.buttons.clicked.connect(self.button_clicked)

    def button_clicked(self, button: QAbstractButton):
        if self.buttons.buttonRole(button) == QDialogButtonBox.AcceptRole:
            favorite = Favorite(name=self.name.text(), description=self.description.text(), path=self.path.text())
            # print(favorite)
            if favorite and favorite.name:
                self.favorite = favorite
                self.accept()
        else:
            self.reject()

    def path_post_action(self, path: str):
        if not self.name.text():
            self.name.setText(path_caption(path=path))

    @classmethod
    def get_favorite(cls, parent, favorite: Favorite = None) -> Favorite:
        dlg = cls(parent=parent, favorite=favorite)
        dlg.exec_()
        return dlg.favorite
