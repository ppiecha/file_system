from PySide2.QtCore import QDir
from PySide2.QtGui import Qt, QMouseEvent
from PySide2.QtWidgets import (
    QDialog,
    QFormLayout,
    QLineEdit,
    QDialogButtonBox,
    QFileDialog,
    QAbstractButton,
)

from src.app.gui.widget import Layout
from src.app.model.favorite import Favorite
from src.app.model.path_util import path_caption


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
        self.path = QLineEdit(favorite.path if favorite else "")
        self.path.mousePressEvent = self.on_get_dir
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

    def on_get_dir(self, e: QMouseEvent):
        path = QFileDialog.getExistingDirectory(
            self, "Select directory", self.path.text() if self.path.text() else QDir.homePath()
        )
        self.path.setText(path)
        if not self.name.text():
            self.name.setText(path_caption(path=path))

    @classmethod
    def get_favorite(cls, parent, favorite: Favorite = None) -> Favorite:
        dlg = cls(parent=parent, favorite=favorite)
        dlg.exec_()
        return dlg.favorite
