from typing import TYPE_CHECKING

from PySide2.QtWidgets import QTabWidget

from src.app.gui.dialog.search.search_panel import SearchPanel
from src.app.utils.path_util import path_caption

if TYPE_CHECKING:
    from src.app.gui.main_form import MainForm


class SearchControl(QTabWidget):
    def __init__(self, parent, mf):
        super().__init__(parent)
        self.mf = mf

    def add_search_panel(self, path: str):
        search_panel = SearchPanel(path=path, parent=self, mf=self.mf)
        self.addTab(search_panel, path_caption(path=path))
