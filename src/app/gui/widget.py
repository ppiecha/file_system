from typing import List

from PySide2.QtWidgets import QBoxLayout, QWidget, QTabWidget


class Layout(QBoxLayout):
    def __init__(self, direction=QBoxLayout.TopToBottom, delta: int = None):
        super().__init__(direction)
        if delta is not None:
            self.setContentsMargins(delta, delta, delta, delta)
            self.setMargin(delta)
            self.setSpacing(delta + 5)


def populated_box_layout(widgets: List[QWidget], direction=QBoxLayout.TopToBottom, delta: int = 0) -> Layout:
    layout = Layout(direction=direction, delta=delta)
    for widget in widgets:
        layout.addWidget(widget)
    return layout


def widget_of_widgets(
    direction: QBoxLayout.Direction = QBoxLayout.TopToBottom, widgets: List[QWidget] = None, delta: int = 0
) -> QWidget:
    widget = QWidget()
    widget.setContentsMargins(delta, delta, delta, delta)
    widget.setLayout(populated_box_layout(direction=direction, widgets=widgets, delta=delta))
    return widget


class TabWidget(QTabWidget):
    def __init__(self, parent):
        super().__init__(parent)
        self.tabBarClicked.connect(self.on_click)

    def on_click(self, index):
        if 0 <= index < self.tabBar().count():
            self.setCurrentIndex(index)

