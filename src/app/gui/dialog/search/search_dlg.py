from PySide2.QtGui import QIcon, QCloseEvent
from PySide2.QtWidgets import QDialog, QBoxLayout

from src.app.gui.dialog.search.search_control import SearchControl


class SearchDlg(QDialog):
    def __init__(self, mf):
        super().__init__(parent=None)
        self.mf = mf
        self.setSizeGripEnabled(True)
        self.setWindowTitle("Search")
        self.setWindowIcon(QIcon("file_system_search.ico"))
        self.search_control = SearchControl(parent=self, mf=mf)
        self.main_box = QBoxLayout(QBoxLayout.TopToBottom, self)
        self.main_box.setContentsMargins(10, 10, 10, 10)
        self.main_box.setSpacing(10)
        self.main_box.addWidget(self.search_control)
        self.setLayout(self.main_box)

        self.win_pos_and_size()

    def closeEvent(self, e: QCloseEvent):
        self.mf.app.search_win_state.x = self.pos().x()
        self.mf.app.search_win_state.y = self.pos().y()
        self.mf.app.search_win_state.width = self.size().width()
        self.mf.app.search_win_state.height = self.size().height()

    def win_pos_and_size(self):
        self.resize(self.mf.app.search_win_state.width, self.mf.app.search_win_state.height)
        self.move(self.mf.app.search_win_state.x, self.mf.app.search_win_state.y)
