import sys

from PySide2.QtWidgets import QApplication

from src.app.gui.main_form import MainForm
from src.app.gui.palette import dark_palette
from src.app.model.schema import App, get_config_file
from src.app.utils.serializer import json_from_file

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")  # Style needed for palette to work
    app.setPalette(dark_palette)
    app_model = App().dict()
    # print(app_model)
    app_model.update(json_from_file(file_name=get_config_file()))
    # print(app_model)
    app_model = App(**app_model)
    main_form = MainForm(app=app_model)
    app.setApplicationName(app_model.name)
    app.setApplicationDisplayName(app_model.name)
    main_form.set_geometry_and_show(app)
    main_form.current_tree().setFocus()
    sys.exit(app.exec_())
