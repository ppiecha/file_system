from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel

from src.app.utils.logger import get_console_logger

logger = get_console_logger(name=__name__)


class Favorite(BaseModel):
    name: str
    description: str = None
    path: str = None
    expanded: bool = False
    children: List[Favorite] = []


Favorite.update_forward_refs()


class Favorites(BaseModel):
    items: List[Favorite] = []
    selected: Optional[Favorite] = None

    def create_item(
        self, current_favorite: Favorite = None, parent_favorite: Favorite = None, new_favorite: Favorite = None
    ):
        if current_favorite:
            current_favorite.children.append(new_favorite)
        else:
            self.items.append(new_favorite)

    def modify_item(self, current_favorite: Favorite, parent_favorite: Favorite = None, new_favorite: Favorite = None):
        current_favorite.name = new_favorite.name
        current_favorite.description = new_favorite.description
        current_favorite.path = new_favorite.path

    def delete_item(self, current_favorite: Favorite, parent_favorite: Favorite = None, new_favorite: Favorite = None):
        def delete_child(current_item: Favorite, to_delete: Favorite):
            current_item.children = [child for child in current_item.children if child is not to_delete]
            for child in current_item.children:
                delete_child(current_item=child, to_delete=to_delete)

        self.items = [item for item in self.items if item is not current_favorite]
        logger.debug(f"top level state {self.items}")
        for item in self.items:
            delete_child(current_item=item, to_delete=current_favorite)

    def sort(self):
        def sort_child(current_favorite: Favorite):
            current_favorite.children = sorted(current_favorite.children, key=lambda i: i.name.lower())
            for child in current_favorite.children:
                sort_child(current_favorite=child)

        self.items = sorted(self.items, key=lambda i: i.name.lower())
        for item in self.items:
            sort_child(current_favorite=item)
