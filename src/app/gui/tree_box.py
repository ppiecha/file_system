from typing import List, Optional, Callable

from PySide2.QtCore import Qt
from PySide2.QtWidgets import QTabWidget, QMenu, QMessageBox

from src.app.gui.action import create_close_tab_action
from src.app.gui.tree_view import TreeView
from src.app.model.path_util import path_caption
from src.app.model.schema import App, Tree
from src.app.utils.constant import APP_NAME
from src.app.utils.logger import get_console_logger

logger = get_console_logger(name=__name__)


class TreeBox(QTabWidget):
    def __init__(self, parent, app_model: App):
        super().__init__(parent=parent)
        self.main_form = parent.parent()
        self.app_model = app_model
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.open_menu)
        self.open_pages()

    def open_menu(self, position):
        menu = QMenu()
        index = self.tabBar().tabAt(position)
        if index >= 0:
            menu.addAction(create_close_tab_action(parent_func=lambda: self, index_func=lambda: index))
        menu.exec_(self.mapToGlobal(position))

    # pylint: disable=unnecessary-comprehension
    def open_pages(self):
        for page in [page for page in self.app_model.pages]:
            logger.debug(f"Opening page {str(page)}")
            self.open_tree_page(pinned_path=page.pinned_path, create=False, find_existing=False)

    def open_tree_page(self, pinned_path: str = None, create: bool = True, find_existing: bool = False):
        if find_existing:
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

    def open_root_page(self):
        self.open_tree_page(pinned_path=None, find_existing=False)

    def add_page(self, tree_model: Tree):
        page = TreeView(parent=self, tree_model=tree_model)
        dir_name = path_caption(path=tree_model.pinned_path) if tree_model.pinned_path else "/"
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
        index = self.currentIndex()
        if index < 0:
            return None
        logger.debug(f"current index {index} pinned path {self.widget(index).pinned_path}")
        return self.widget(index)

    def close_page(self, index_func: Callable):
        index = index_func()
        if index == -1:
            QMessageBox.information(self.parent(), APP_NAME, "No tab selected")
            return
        page = self.widget(index)
        self.app_model.remove_page(page=page.tree_model)
        page.deleteLater()
        self.removeTab(index)

    def tabRemoved(self, index):
        logger.debug(f"Deleted widget with index {index}")
