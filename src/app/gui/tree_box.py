from typing import List, Optional

from PySide2.QtWidgets import QTabWidget

from src.app.gui.tree_view import TreeView
from src.app.model.path_util import path_caption
from src.app.model.schema import App, Tree
from src.app.utils.logger import get_console_logger

logger = get_console_logger(name=__name__)


class TreeBox(QTabWidget):
    def __init__(self, parent, app_model: App):
        super().__init__(parent=parent)
        # self.setTabsClosable(True)
        self.app_model = app_model
        self.open_pages()

    # pylint: disable=unnecessary-comprehension
    def open_pages(self):
        for page in [page for page in self.app_model.pages]:
            logger.debug(f"Opening page {str(page)}")
            self.open_tree_page(pinned_path=page.pinned_path, create=False)

    def open_tree_page(self, pinned_path: str = None, create: bool = True):
        page = self.page(path=pinned_path)
        if page:
            self.setCurrentIndex(self.indexOf(page))
            return
        if create:
            tree_model = self.app_model.add_page(pinned_path=pinned_path)
        else:
            tree_model = self.app_model.get_page_by_pinned_path(pinned_path=pinned_path)
            tree_model = tree_model or Tree(pinned_path=pinned_path)
        self.add_page(tree_model=tree_model)

    def add_page(self, tree_model: Tree):
        page = TreeView(parent=self, tree_model=tree_model)
        dir_name = path_caption(path=tree_model.pinned_path) if tree_model.pinned_path else "root"
        self.addTab(page, dir_name)

    def pages(self) -> List[TreeView]:
        return [self.widget(i) for i in range(self.count())]

    def page(self, path: str) -> Optional[TreeView]:
        # logger.debug(f"search page {[page for page in self.pages() if page.pinned_path == path]}")
        pages = [page for page in self.pages() if page.pinned_path == path]
        if len(pages) == 0:
            return None
        if len(pages) > 1:
            raise RuntimeError(f"Found for than one page with path {path}")
        return pages[0]

    def current_tree(self) -> Optional[TreeView]:
        return self.currentWidget()
