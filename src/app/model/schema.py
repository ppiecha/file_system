from typing import Optional, List

from pydantic import BaseModel

from src.app.model.favorite import Favorites
from src.app.utils.constant import APP_NAME

CONFIG_FILE = "file_system.json"


class Tree(BaseModel):
    root_path: Optional[str] = None
    current_path: Optional[str] = None
    pinned_path: Optional[str] = None
    visible_columns: List[int] = []
    hide_header: bool = True
    show_files: bool = True
    show_hidden: bool = False
    show_system: bool = False


class App(BaseModel):
    name: str = APP_NAME
    pages: List[Tree] = []
    favorites: Favorites = Favorites()

    def add_page(self, pinned_path: str = None) -> Tree:
        tree = Tree(pinned_path=pinned_path)
        self.pages.append(tree)
        return tree
