from typing import Optional, List

from pydantic import BaseModel

from src.app.model.favorite import Favorites
from src.app.utils.constant import APP_NAME
from src.app.utils.logger import get_console_logger

CONFIG_FILE = "file_system.json"

logger = get_console_logger(name=__name__)


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
    is_maximized: bool = False
    on_top: bool = False
    splitter_sizes: Optional[List[int]] = None
    show_favorites: bool = True


class SysPath(BaseModel):
    path: str = None
    view: bool = True
    edit: bool = True


class SysPaths(BaseModel):
    notepad: SysPath = SysPath()
    vs_code: SysPath = SysPath()
    chrome: SysPath = SysPath()


class App(BaseModel):
    name: str = APP_NAME
    pages: List[Tree] = []
    favorites: Favorites = Favorites()
    win_state: WindowState = WindowState()
    sys_paths: Optional[SysPaths] = SysPaths()

    def add_page(self, pinned_path: str = None) -> Tree:
        tree = Tree(pinned_path=pinned_path)
        self.pages.append(tree)
        return tree

    def get_page_by_pinned_path(self, pinned_path: str) -> Optional[Tree]:
        pages = [page for page in self.pages if page.pinned_path == pinned_path]
        return pages[0] if pages else None

    def remove_page(self, page: Tree):
        self.pages.remove(page)
        logger.debug(f"Page removed {page}")
