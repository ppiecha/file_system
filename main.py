import sys

from PySide6.QtWidgets import QApplication

from src.app.gui.main_form import MainForm
from src.app.gui.palette import dark_palette
from src.app.model.schema import get_config_file, App
from src.app.utils.serializer import json_from_file

if __name__ == "__main__":
    app_qt_object = QApplication(sys.argv)
    app_qt_object.setStyle("Fusion")  # Style needed for palette to work
    app_qt_object.setPalette(dark_palette)
    app_model = App().dict()
    app_model.update(json_from_file(file_name=get_config_file()))
    app_model = App(**app_model)
    main_form = MainForm(app=app_model, app_qt_object=app_qt_object)
    # app_qt_object.setApplicationName(app_model.name)
    # app_qt_object.setApplicationDisplayName(app_model.name)
    main_form.set_geometry_and_show(app_qt_object)
    main_form.current_tree().setFocus()
    sys.exit(app_qt_object.exec())
