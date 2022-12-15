from PySide2.QtWidgets import QLineEdit, QAbstractButton, QDialogButtonBox, QMessageBox
from pydantic import BaseModel

from src.app.gui.dialog.base import FormDialog, Properties, PathEdit
from src.app.model.favorite import Favorite
from src.app.utils.path_util import path_caption


class FavoriteDialog(FormDialog):
    def populate_form(self, properties: Properties):
        self.components["name"] = QLineEdit(self.properties.get("name"))
        self.components["description"] = QLineEdit(self.properties.get("description"))
        self.components["path"] = PathEdit(text=self.properties.get("path"), post_action=self.path_post_action)
        self.form.addRow("Name", self.components["name"])
        self.form.addRow("Description", self.components["description"])
        self.form.addRow("Path", self.components["path"])

    def validate_input(self) -> bool:
        return self.components["name"].text() and self.components["path"].text()

    def get_entity(self) -> BaseModel:
        entity_dict = {
            key: self.components[key].text() for key in self.properties.keys() if key in ["name", "description", "path"]
        }
        return self.entity.__class__(**entity_dict)

    def on_button_clicked(self, button: QAbstractButton):
        if self.buttons.buttonRole(button) == QDialogButtonBox.AcceptRole:
            if self.validate_input():
                self.accept()
            else:
                QMessageBox.warning(self, "Missing required parameters", "Name and path are mandatory")
        else:
            self.reject()

    def path_post_action(self, path: str):
        if not self.components["name"].text():
            self.components["name"].setText(path_caption(path=path))

    @classmethod
    def get_favorite(cls, parent, favorite: Favorite = None) -> BaseModel:
        dlg = cls(parent=parent, entity=favorite if favorite else Favorite(), caption="Edit favorite")
        # dlg = cls(parent=parent, entity=favorite, caption="Edit favorite")
        dlg.exec_()
        return dlg.get_entity()
