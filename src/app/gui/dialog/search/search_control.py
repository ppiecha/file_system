from typing import TYPE_CHECKING, Dict

from PySide2.QtWidgets import QTabWidget, QAction

from src.app.gui.action.command import create_go_to_action
from src.app.gui.dialog.search.search_panel import SearchPanel

if TYPE_CHECKING:
    from src.app.gui.main_form import MainForm


class SearchControl(QTabWidget):
    def __init__(self, parent, mf):
        super().__init__(parent)
        self.search_dlg = parent
        self.mf = mf
        self.search_actions: Dict[str, QAction] = {}
        self.init_search_actions()

        self.currentChanged.connect(self.on_current_changed)

    def init_search_actions(self):
        go_to_action = create_go_to_action(
            parent_func=self.mf.current_tree, path_func=self.mf.path_func, context_func=self.mf.context_func
        )
        go_to_action.setText("Go to item")
        self.search_actions = {
            "go_to_item": go_to_action
        }

    def add_search_panel(self, path: str):
        index = self.index_of_path(path=path)
        if index != -1:
            self.make_active(index=index)
            return
        search_panel = SearchPanel(path=path, parent=self, mf=self.mf)
        index = self.addTab(search_panel, search_panel.search_path_caption())
        self.setCurrentIndex(index)
        self.mf.search_dlg.activateWindow()

    def make_active(self, index: int):
        self.mf.search_dlg.activateWindow()
        self.setCurrentIndex(index)
        search_panel = self.widget(index)
        search_panel.search_btn.setDefault(True)
        search_panel.search_btn.setFocus()
        search_panel.widget_map["keyword"].setFocus()
        search_panel.widget_map["keyword"].selectAll()

    def on_current_changed(self, index):
        self.make_active(index=index)

    def index_of_path(self, path: str) -> int:
        for index in range(self.count()):
            if self.widget(index).search_path() == path:
                return index
        return -1

    def rename_tab(self, search_panel: SearchPanel):
        index = self.indexOf(search_panel)
        self.setTabText(index, search_panel.search_path_caption())
