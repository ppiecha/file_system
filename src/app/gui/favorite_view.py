from __future__ import annotations

import logging
from functools import partial
from typing import List, Callable, Optional
from enum import Enum, auto

from PySide6.QtCore import QPoint, QEvent
from PySide6.QtGui import Qt, QFocusEvent
from PySide6.QtWidgets import QTreeWidgetItem, QAbstractItemView, QMenu, QMessageBox, QTreeWidget

from src.app.gui.action.command import Action
from src.app.gui.dialog.favorite_edit import FavoriteDialog
from src.app.model.favorite import Favorite, Favorites
from src.app.utils.constant import APP_NAME
from src.app.utils.path_util import all_folders, path_caption
from src.app.model.schema import Group
from src.app.utils.logger import get_console_logger


logger = get_console_logger(name=__name__, log_level=logging.ERROR)


class EditMode(Enum):
    CREATE = auto()
    EDIT = auto()
    DELETE = auto()


class FavoriteTree(QTreeWidget):
    def __init__(self, parent, group: Group):
        super().__init__(parent=parent)
        self.favorites = group.favorites
        self.group_panel = parent.parent()
        self.group_box = self.group_panel.parent()
        self.main_form = self.group_box.main_form
        self.init_ui()
        self.recreate()

    def init_ui(self):
        self.setAcceptDrops(True)
        self.setHeaderHidden(True)
        self.setSelectionMode(QAbstractItemView.SingleSelection)
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        # self.clicked.connect(self.on_clicked)
        # self.doubleClicked.connect(self.on_double_clicked)
        self.itemActivated.connect(self.on_item_activated)
        self.customContextMenuRequested.connect(self.open_menu)
        self.itemExpanded.connect(lambda item: self.expanded(item=item))
        # self.expanded.connect(self.expanded)
        self.itemCollapsed.connect(lambda item: self.collapsed(item=item))
        # self.collapsed.connect(self.collapsed)
        self.itemSelectionChanged.connect(self.selection_changed)

    def remove_dead_entries(self):
        removed = self.favorites.remove_dead_entries()
        if removed:
            path_lst = "\n".join(removed)
            QMessageBox().information(
                self, APP_NAME, f"The following paths are not longer valid and have been removed \n{path_lst}"
            )
            self.recreate()

    def focusInEvent(self, event: QFocusEvent) -> None:
        super().focusInEvent(event)
        logger.debug("focusInEvent")
        self.remove_dead_entries()

    def enterEvent(self, event: QEvent) -> None:
        super().enterEvent(event)
        logger.debug("enterEvent")
        self.remove_dead_entries()

    def current_favorite(self) -> Optional[Favorite]:
        item = self.currentItem()
        if item:
            return self.get_favorite(item)
        return None

    # pylint: disable=unused-argument)
    def on_item_activated(self, item: QTreeWidgetItem, column: int):
        favorite = self.get_favorite(item)
        if not favorite:
            raise ValueError(f"Cannot get favorite from item {item}")
        logger.debug(f"Open favorite path {favorite.path}")
        self.main_form.current_tree_box().open_tree_page(pinned_path=favorite.path, find_existing=True, go_to_page=True)

    def selection_changed(self):
        items = self.selectedItems()
        item = items[0] if items else None
        if item:
            self.favorites.selected = self.get_favorite(item)
            # logger.debug(f"selected {self.favorites.selected.dict()}")

    def get_favorite(self, item: QTreeWidgetItem) -> Favorite:
        return item.data(0, Qt.UserRole)

    # pylint: disable=unused-argument
    def expanded(self, item: QTreeWidgetItem):
        self.get_favorite(item).expanded = True

    def collapsed(self, item: QTreeWidgetItem):
        self.get_favorite(item).expanded = False

    def save_to_file(self):
        self.main_form.save_settings()

    def recreate(self):
        self.clear()
        self.favorites.sort()
        self.insertTopLevelItems(0, self.create_items(self.favorites))

    def create_items(self, favorites: Favorites) -> List[QTreeWidgetItem]:
        items = []
        for favorite in favorites.items:
            item = self.create_top_level_item(favorite=favorite)
            self.create_children(parent=item, children=favorite.children)
            items.append(item)
        return items

    def populate_favorite_item(self, item: QTreeWidgetItem, favorite: Favorite):
        item.setText(0, favorite.name)
        item.setText(1, favorite.description)
        item.setText(2, favorite.path)
        item.setData(0, Qt.UserRole, favorite)
        item.setIcon(0, self.main_form.icons["dir"])
        return item

    def create_top_level_item(self, favorite: Favorite) -> QTreeWidgetItem:
        item = QTreeWidgetItem(self)
        self.populate_favorite_item(item=item, favorite=favorite)
        if self.favorites.selected and favorite.dict() == self.favorites.selected.dict():
            self.set_item_selected(item)
        return item

    def set_item_selected(self, item: QTreeWidgetItem):
        self.setCurrentItem(item)
        self.scrollToItem(item)

    def create_children(self, parent: QTreeWidgetItem, children: List[Favorite]) -> QTreeWidgetItem:
        for child in children:
            item = QTreeWidgetItem(parent)
            self.populate_favorite_item(item=item, favorite=child)
            if parent.data(0, Qt.UserRole).expanded:
                self.expandItem(parent)
            if self.favorites.selected and child.dict() == self.favorites.selected.dict():
                self.set_item_selected(item)
            self.create_children(parent=item, children=child.children)
        return parent

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls() and all_folders([u.toLocalFile() for u in event.mimeData().urls()]):
            event.accept()
        else:
            event.ignore()

    def dragMoveEvent(self, event):
        if event.mimeData().hasUrls() and all_folders([u.toLocalFile() for u in event.mimeData().urls()]):
            event.accept()
        else:
            event.ignore()

    def dropEvent(self, event):
        item: QTreeWidgetItem = self.itemAt(event.pos())
        files = [u.toLocalFile() for u in event.mimeData().urls()]
        new_favorites = [Favorite(name=path_caption(path=file), path=file) for file in files]
        if item:
            current_favorite = self.get_favorite(item=item)
            for new_favorite in new_favorites:
                self.favorites.create_item(current_favorite=current_favorite, new_favorite=new_favorite)
            self.create_children(parent=item, children=new_favorites)
        else:
            for new_favorite in new_favorites:
                self.favorites.create_item(new_favorite=new_favorite)
        self.recreate()
        logger.debug(f"Favorites after drop {self.favorites}")

    def open_menu(self, position: QPoint):
        items = self.selectedItems()
        parent_item = items[0] if items else None
        menu = FavoriteTree.Menu(favorite_tree=self, current_item=parent_item)
        menu.open_menu(position=position)

    class Menu(QMenu):
        def __init__(self, favorite_tree: FavoriteTree, current_item: QTreeWidgetItem):
            super().__init__(parent=None)
            self.favorite_tree = favorite_tree
            self.current_item = current_item

        def save_tree_and_recreate(self):
            self.favorite_tree.save_to_file()
            self.favorite_tree.recreate()

        def modifier(self, current_item: QTreeWidgetItem, parent_item: QTreeWidgetItem, func: Callable, mode: EditMode):
            favorite = None
            current_favorite = self.favorite_tree.get_favorite(current_item) if current_item else None
            parent_favorite = self.favorite_tree.get_favorite(parent_item) if parent_item else None
            if mode in (EditMode.CREATE, EditMode.EDIT):
                favorite = FavoriteDialog.get_favorite(
                    parent=self.favorite_tree, favorite=current_favorite if mode == EditMode.EDIT else None
                )
            if favorite or mode == EditMode.DELETE:
                if current_favorite and mode == EditMode.CREATE:
                    current_favorite.expanded = True
                func(current_favorite=current_favorite, parent_favorite=parent_favorite, new_favorite=favorite)
                if mode == EditMode.DELETE:
                    selected = parent_favorite
                elif mode == EditMode.EDIT:
                    selected = current_favorite
                else:
                    selected = favorite
                self.favorite_tree.favorites.selected = selected
                # logger.debug(f"selected after operation {self.favorite_tree.favorites.selected}")
                self.save_tree_and_recreate()

        def open_menu(self, position: QPoint):
            self.clear()
            self.addAction(
                Action(
                    parent=self,
                    caption="Create top level item",
                    slot=partial(self.modifier, None, None, self.favorite_tree.favorites.create_item, EditMode.CREATE),
                )
            )
            if self.current_item:
                self.addAction(
                    Action(
                        parent=self,
                        caption="Create sub-item",
                        slot=partial(
                            self.modifier,
                            self.current_item,
                            self.current_item.parent(),
                            self.favorite_tree.favorites.create_item,
                            EditMode.CREATE,
                        ),
                    )
                )
                self.addAction(
                    Action(
                        parent=self,
                        caption="Edit item",
                        slot=partial(
                            self.modifier,
                            self.current_item,
                            self.current_item.parent(),
                            self.favorite_tree.favorites.modify_item,
                            EditMode.EDIT,
                        ),
                    )
                )
                self.addAction(
                    Action(
                        parent=self,
                        caption="Delete item",
                        slot=partial(
                            self.modifier,
                            self.current_item,
                            self.current_item.parent(),
                            self.favorite_tree.favorites.delete_item,
                            EditMode.DELETE,
                        ),
                    )
                )
            self.exec_(self.favorite_tree.viewport().mapToGlobal(position))
