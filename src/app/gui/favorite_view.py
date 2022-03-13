from __future__ import annotations
import sys
from functools import partial
from typing import List

from PySide2.QtCore import QPoint
from PySide2.QtGui import Qt
from PySide2.QtWidgets import QWidget, QTreeWidget, QApplication, QTreeWidgetItem, QAbstractItemView, QMenu

from src.app.gui.action import Action
from src.app.gui.dialog import FavoriteDlg
from src.app.gui.palette import dark_palette
from src.app.model.favorite import Favorite, Favorites
from src.app.utils.logger import get_console_logger
from src.app.utils.serializer import json_to_file, json_from_file


logger = get_console_logger(name=__name__)


class FavoriteTree(QTreeWidget):
    def __init__(self, parent, favorites: Favorites):
        super().__init__(parent=parent)
        self.favorites = favorites
        self.setHeaderLabels(["Name", "Description", "Path"])
        self.setSelectionMode(QAbstractItemView.SingleSelection)
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.recreate()

        # self.clicked.connect(self.on_clicked)
        # self.doubleClicked.connect(self.on_double_clicked)
        self.customContextMenuRequested.connect(self.show_menu)
        self.itemExpanded.connect(self.expanded)
        self.itemCollapsed.connect(self.collapsed)
        self.itemSelectionChanged.connect(self.selection_changed)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.save_to_file()
        logger.debug("saved")

    def selection_changed(self):
        items = self.selectedItems()
        item = items[0] if items else None
        if item:
            self.favorites.selected = item.data(0, Qt.UserRole)
            print(self.favorites.selected.dict())

    def expanded(self, item: QTreeWidgetItem):
        item.data(0, Qt.UserRole).expanded = True

    def collapsed(self, item: QTreeWidgetItem):
        item.data(0, Qt.UserRole).expanded = False

    def save_to_file(self):
        json_to_file(json_dict=self.favorites.dict(), file_name="favorites.json")

    def recreate(self):
        self.favorites = Favorites(**json_from_file(file_name="favorites.json"))
        self.clear()
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
        return item

    def create_top_level_item(self, favorite: Favorite) -> QTreeWidgetItem:
        item = QTreeWidgetItem(self)
        self.populate_favorite_item(item=item, favorite=favorite)
        if self.favorites.selected and favorite.dict() == self.favorites.selected.dict():
            self.set_item_selected(item)
        return item

    def set_item_selected(self, item: QTreeWidgetItem):
        self.setItemSelected(item, True)
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

    def show_menu(self, position: QPoint):
        items = self.selectedItems()
        parent_item = items[0] if items else None
        with FavoriteTree.Menu(favorite_tree=self, parent_item=parent_item) as menu:
            menu.open_menu(position=position)

    class Menu(QMenu):
        def __init__(self, favorite_tree: FavoriteTree, parent_item: QTreeWidgetItem):
            super().__init__(parent=favorite_tree)
            self.favorite_tree = favorite_tree
            self.parent_item = parent_item

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc_val, exc_tb):
            pass

        def save_tree_and_recreate(self):
            self.favorite_tree.save_to_file()
            self.favorite_tree.recreate()

        def creator(self, parent_item: QTreeWidgetItem):
            favorite = FavoriteDlg.get_favorite(parent=self.favorite_tree)
            if favorite:
                self.favorite_tree.favorites.selected = favorite
                parent_favorite = parent_item.data(0, Qt.UserRole) if parent_item else None
                if parent_favorite:
                    parent_favorite.expanded = True
                self.favorites.create_item(item=favorite, parent=parent_favorite)
                self.save_tree_and_recreate()

        def open_menu(self, position: QPoint):
            self.clear()
            self.addAction(
                Action(
                    parent=self,
                    caption="Create top level item",
                    slot=partial(self.creator, None),
                )
            )
            if self.parent_item:
                self.addAction(
                    Action(
                        parent=self,
                        caption="Create sub-item",
                        slot=partial(self.creator, self.parent_item),
                    )
                )
            self.exec_(self.favorite_tree.viewport().mapToGlobal(position))


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")  # Style needed for palette to work
    app.setPalette(dark_palette)
    with FavoriteTree(
        parent=None,
        favorites=Favorites(
            items=[Favorite(name="First", description="desc", path="c:", children=[Favorite(name="Second")])]
        ),
    ) as tree:
        tree.show()
        sys.exit(app.exec_())
