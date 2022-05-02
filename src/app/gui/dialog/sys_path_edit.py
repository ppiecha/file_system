import logging

from PySide2.QtWidgets import QAbstractButton, QDialogButtonBox
from pydantic import BaseModel

from src.app.gui.dialog.base import FormDialog, Properties, FileEdit
from src.app.model.schema import SysPath, SysPaths
from src.app.utils.logger import get_console_logger

logger = get_console_logger(name=__name__, log_level=logging.DEBUG)


class SysPathDialog(FormDialog):
    def populate_form(self, properties: Properties):
        logger.debug(f"props {properties}")
        self.components["notepad"] = FileEdit(text=properties.get("notepad")["path"])
        self.components["vs_code"] = FileEdit(text=properties.get("vs_code")["path"])
        self.components["chrome"] = FileEdit(text=properties.get("chrome")["path"])
        self.form.addRow("Notepad", self.components["notepad"])
        self.form.addRow("VS Code", self.components["vs_code"])
        self.form.addRow("Chrome", self.components["chrome"])

    def validate_input(self) -> bool:
        return True

    def get_entity(self) -> BaseModel:
        entity_dict = {
            key: SysPath(path=self.components[key].text())
            for key in self.properties.keys()
            if key in ["notepad", "vs_code", "chrome"]
        }
        return self.entity.__class__(**entity_dict)

    def on_button_clicked(self, button: QAbstractButton):
        if self.buttons.buttonRole(button) == QDialogButtonBox.AcceptRole:
            self.parent().app.sys_paths = self.get_entity()
            self.parent().save_settings()
            self.accept()
        else:
            self.reject()

    @classmethod
    def exec(cls, parent, sys_paths: SysPaths = None) -> None:
        dlg = cls(parent=parent, entity=sys_paths if sys_paths else SysPaths(), caption="Edit system apps")
        dlg.exec_()
