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
        def delete_child(current_favorite: Favorite):
            current_favorite.children = [child for child in current_favorite.children if child is not current_favorite]
            for child in current_favorite.children:
                delete_child(current_favorite=child)

        self.items = [item for item in self.items if item is not current_favorite]
        for item in self.items:
            delete_child(current_favorite=item)
