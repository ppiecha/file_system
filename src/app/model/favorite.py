from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel


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

    def create_item(self, item: Favorite, parent: Favorite = None):
        if parent:
            parent.children.append(item)
        else:
            self.items.append(item)
