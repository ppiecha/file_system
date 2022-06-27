from PySide2.QtWidgets import QDialog, QBoxLayout

from src.app.gui.dialog.search.search_control import SearchControl


class SearchDlg(QDialog):
    def __init__(self, mf):
        super().__init__(parent=None)
        self.mf = mf
        self.setSizeGripEnabled(True)
        self.search_control = SearchControl(parent=self, mf=mf)
        self.main_box = QBoxLayout(QBoxLayout.TopToBottom, self)
        self.main_box.setContentsMargins(10, 10, 10, 10)
        self.main_box.setSpacing(10)
        self.main_box.addWidget(self.search_control)
        self.setLayout(self.main_box)

    def closeEvent(self, _):
        pass
        # Save positions and successful parameters. Destroy search on main exit
        # self.config.mf.config.setValue(IniAttr.EVENT_WIN_SIZE, self.size())
        # self.config.mf.config.setValue(IniAttr.EVENT_WIN_POS, self.pos())
