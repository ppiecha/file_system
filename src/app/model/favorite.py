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

    def create_item(self, favorite: Favorite, parent_favorite: Favorite = None, new_favorite: Favorite = None):
        if parent_favorite:
            parent_favorite.children.append(new_favorite)
        else:
            self.items.append(new_favorite)

    def modify_item(self, favorite: Favorite, parent_favorite: Favorite = None, new_favorite: Favorite = None):
        favorite.name = new_favorite.name
        favorite.description = new_favorite.description
        favorite.path = new_favorite.path

    def delete_item(self, favorite: Favorite, parent_favorite: Favorite = None, new_favorite: Favorite = None):
        logger.debug(f"item to delete {id(favorite)} {favorite}")
        def delete_child(current_favorite: Favorite):
            logger.debug(f"checking children of {id(current_favorite)} {current_favorite} {[id(child) for child in current_favorite.children]}")
            current_favorite.children = [child for child in current_favorite.children if child is not favorite]
            for child in current_favorite.children:
                delete_child(current_favorite=child)

        self.items = [item for item in self.items if item is not favorite]
        for favorite in self.items:
            delete_child(current_favorite=favorite)
