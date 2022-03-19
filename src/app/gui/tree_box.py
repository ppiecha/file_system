import sys
from typing import List, Optional

from PySide2.QtWidgets import QWidget, QApplication, QTabWidget

from src.app.gui.filter import FilterView
from src.app.gui.palette import dark_palette
from src.app.gui.tree import TreeView
from src.app.model.path import path_caption
from src.app.model.schema import Tree, App


class TreeBox(QTabWidget):
    def __init__(self, parent, app_model: App):
        super().__init__(parent=parent)
        self.app_model = app_model

    def open_tree_page(self, pinned_path: str = None):
        if pinned_path:
            page = self.page(path=pinned_path)
            if page:
                self.setCurrentIndex(self.indexOf(page))
                return
        self.add_page(pinned_path=pinned_path)

    def add_page(self, pinned_path: str = None):
        tree_model = self.app_model.add_page(pinned_path=pinned_path)
        page = TreeView(parent=self, tree_model=tree_model)
        dir_name = path_caption(path=pinned_path) if pinned_path else "not defined"
        self.addTab(page, dir_name)

    def pages(self) -> List[TreeView]:
        return [self.widget(i) for i in range(self.count())]

    def page(self, path: str) -> Optional[TreeView]:
        pages = [page for page in self.pages() if page.pinned_path == path]
        if len(pages) == 0:
            return None
        if len(pages) > 1:
            raise RuntimeError(f"Found for than one page with path {path}")
        return pages[0]


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")  # Style needed for palette to work
    app.setPalette(dark_palette)
    tree = TreeBox(None)
    tree.show()
    sys.exit(app.exec_())
