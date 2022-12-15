from typing import List

from PySide2.QtWidgets import QBoxLayout, QWidget


class Layout(QBoxLayout):
    def __init__(self, direction=QBoxLayout.TopToBottom, delta: int = None):
        super().__init__(direction)
        if delta is not None:
            self.setContentsMargins(delta, delta, delta, delta)
            self.setMargin(delta)
            self.setSpacing(delta + 5)


def populated_box_layout(widgets: List[QWidget], direction = QBoxLayout.TopToBottom, delta: int = 0) -> Layout:
    layout = Layout(direction=direction, delta=delta)
    for widget in widgets:
        layout.addWidget(widget, stretch=1)
    return layout
