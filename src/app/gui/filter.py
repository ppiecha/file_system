from PySide6.QtWidgets import QWidget, QBoxLayout, QLabel, QLineEdit

from src.app.gui.widget import Layout


class FilterView(QWidget):
    def __init__(self, parent):
        super().__init__(parent=parent)
        self.parent = parent
        layout = Layout(QBoxLayout.LeftToRight)
        layout.addStretch()
        layout.addWidget(QLabel(" Filter "))
        edit = QLineEdit()
        edit.textChanged.connect(self.on_text_changed)
        layout.addWidget(edit)
        self.setLayout(layout)

    def on_text_changed(self, text: str):
        filters = text.split(";")
        self.parent.model().setNameFilters(filters if filters else "*")
        self.parent.model().setNameFilterDisables(False)
