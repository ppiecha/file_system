import sys

from PySide2.QtWidgets import QWidget, QApplication

from src.app.gui.filter import FilterView
from src.app.gui.palette import dark_palette
from src.app.gui.tree import TreeView
from src.app.gui.widget import Layout
from src.app.model.schema import Tree


class TreeTab(QWidget):
    def __init__(self, parent: TreeView):
        super().__init__(parent=parent)
        layout = Layout()
        self.tree = TreeView(parent=None, tree=Tree(root_path="c:\\", current_path="c:\\Users\\piotr\\temp"))
        layout.addWidget(self.tree)
        layout.addWidget(FilterView(parent=self.tree))
        self.setLayout(layout)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")  # Style needed for palette to work
    app.setPalette(dark_palette)
    tree = TreeTab(None)
    tree.show()
    sys.exit(app.exec_())
