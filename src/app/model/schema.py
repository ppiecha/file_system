from typing import Optional, List

from pydantic import BaseModel

from src.app.model.favorite import Favorites
from src.app.utils.constant import APP_NAME

CONFIG_FILE = "file_system.json"


class Tree(BaseModel):
    current_path: Optional[str] = None
    pinned_path: Optional[str] = None
    visible_columns: List[int] = []
    hide_header: bool = True
    show_files: bool = True
    show_hidden: bool = False
    show_system: bool = False


class WindowState(BaseModel):
    x: int = 200
    y: int = 200
    width: int = 500
    height: int = 300
    state: int = None
    on_top: bool = False
    splitter_sizes: Optional[List[int]] = None
    show_favorites: bool = True


class App(BaseModel):
    name: str = APP_NAME
    pages: List[Tree] = []
    favorites: Favorites = Favorites()
    win_state: WindowState = WindowState()

    def add_page(self, pinned_path: str = None) -> Tree:
        tree = Tree(pinned_path=pinned_path)
        self.pages.append(tree)
        return tree

    def get_page_by_pinned_path(self, pinned_path: str) -> Optional[Tree]:
        pages = [page for page in self.pages if page.pinned_path == pinned_path]
        return pages[0] if pages else None
