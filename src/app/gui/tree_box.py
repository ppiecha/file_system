import logging
from typing import List, Optional, Callable

from PySide6.QtCore import Qt, QDir
from PySide6.QtWidgets import QMenu, QMessageBox, QFileDialog

from src.app.gui.action.tab import create_close_tab_action, create_close_all_tabs_action
from src.app.gui.tree_view import TreeView
from src.app.gui.widget import TabWidget
from src.app.utils.path_util import path_caption
from src.app.model.schema import Group, Tree
from src.app.utils.constant import APP_NAME
from src.app.utils.logger import get_console_logger

logger = get_console_logger(name=__name__, log_level=logging.ERROR)


class TreeBox(TabWidget):
    def __init__(self, parent, group: Group):
        super().__init__(parent=parent)
        self.group_panel = self.parent().parent()
        self.group_box = self.group_panel.parent()
        self.main_form = self.group_box.main_form
        self.group = group
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.open_menu)
        self.currentChanged.connect(self.on_current_changed)
        self.open_pages()

    def open_menu(self, position):
        menu = QMenu()
        index = self.tabBar().tabAt(position)
        if index >= 0:
            menu.addAction(create_close_tab_action(parent_func=lambda: self, index_func=lambda: index))
            menu.addAction(create_close_all_tabs_action(parent_func=lambda: self))
        menu.exec_(self.mapToGlobal(position))

    # pylint: disable=unnecessary-comprehension
    def open_pages(self):
        if not self.group.pages:
            self.open_root_page(find_existing=True)
            return
        for page in self.group.pages:
            logger.info(f"Opening page {str(page.pinned_path)} last path {self.group.last_page_pinned_path}")
            self.open_tree_page(pinned_path=page.pinned_path, create=False, find_existing=False)
        if pinned_path := self.group.last_page_pinned_path:
            self.go_to_page(pinned_path=pinned_path)

    def open_tree_page(
        self,
        pinned_path: str = None,
        create: bool = True,
        find_existing: bool = False,
        go_to_page: bool = False,
        selection: List[str] = None,
    ):
        selected_path = selection[0] if selection and len(selection) == 1 else None
        if find_existing:
            page = self.page(path=pinned_path)
            if page:
                self.setCurrentIndex(self.indexOf(page))
                current_tree = self.current_tree()
                if current_tree and selected_path:
                    current_tree.current_path = selected_path
                return
        if create:
            tree_model = self.group.add_page(pinned_path=pinned_path)
        else:
            tree_model = self.group.get_page_by_pinned_path(pinned_path=pinned_path)
            tree_model = tree_model or Tree(pinned_path=pinned_path)
        self.add_page(
            tree_model=tree_model,
            go_to_page=go_to_page,
            last_selected_path=tree_model.last_selected_path or selected_path,
        )

    def open_root_page(self, find_existing: bool = True):
        self.open_tree_page(pinned_path=None, find_existing=find_existing, go_to_page=True)

    def open_user_defined_page(self):
        path = QFileDialog.getExistingDirectory(self, APP_NAME, QDir.homePath())
        if path:
            self.open_tree_page(pinned_path=path, find_existing=True, go_to_page=True)

    def add_page(self, tree_model: Tree, go_to_page: bool = False, last_selected_path: List[str] = None):
        page = TreeView(parent=self, tree_model=tree_model, last_selected_path=last_selected_path)
        dir_name = path_caption(path=tree_model.pinned_path) if tree_model.pinned_path else "/"
        self.addTab(page, dir_name)
        if go_to_page:
            self.go_to_page(pinned_path=tree_model.pinned_path)

    def pages(self) -> List[TreeView]:
        return [self.widget(i) for i in range(self.count())]

    def page(self, path: str) -> Optional[TreeView]:
        # logger.debug(f"search page {[page for page in self.pages() if page.pinned_path == path]}")
        pages = [page for page in self.pages() if page.pinned_path == path]
        if len(pages) == 0:
            return None
        if len(pages) > 1:
            raise RuntimeError(f"Found more for than one page with path {path}")
        return pages[0]

    def go_to_page(self, pinned_path: str):
        page = self.page(path=pinned_path)
        if page:
            self.setCurrentIndex(self.indexOf(page))

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
        self.group.remove_page(page=page.tree_model)
        page.deleteLater()
        self.removeTab(index)
        if self.count() == 0:
            self.open_root_page()

    def close_all_pages(self):
        if self.count() > 0:
            for index in range(self.count() - 1, -1, -1):
                self.close_page(index_func=lambda x=index: x)

    def tabRemoved(self, index):
        if current_tree := self.current_tree():
            current_tree.setFocus()
            logger.debug(
                f"Deleted widget with index {index} " f"focus set to {path_caption(self.current_tree().current_path)}"
            )

    def on_current_changed(self, index: int):
        if current_tree := self.current_tree():
            current_tree.set_selection()

    def store_pages_layout(self):
        for page in self.pages():
            page.store_layout()
