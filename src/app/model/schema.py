import logging
from typing import Optional, List

from PySide6.QtCore import QDir
from pydantic import BaseModel

from src.app.model.favorite import Favorites
from src.app.utils.constant import APP_NAME, USER_NAME
from src.app.utils.logger import get_console_logger
from src.app.utils.shell import join, get_app_data_path

logger = get_console_logger(name=__name__, log_level=logging.ERROR)


def get_config_file() -> str:
    path = join(items=[get_app_data_path(), USER_NAME, APP_NAME])
    app_data = QDir(path)
    if not app_data.exists():
        app_data.mkpath(path)
    return join(items=[path, "file_system.json"])


class Tree(BaseModel):
    current_path: Optional[str] = None
    pinned_path: Optional[str] = None
    visible_columns: List[int] = []
    hide_header: bool = True
    show_files: bool = True
    show_hidden: bool = False
    show_system: bool = False
    expanded_items: List[str] = []
    last_selected_path: Optional[str] = None


class WindowState(BaseModel):
    x: int = 200
    y: int = 200
    width: int = 500
    height: int = 300
    is_maximized: bool = False
    on_top: bool = False
    splitter_sizes: Optional[List[int]] = None
    show_favorites: bool = True


class SearchWindowState(BaseModel):
    x: int = 200
    y: int = 200
    width: int = 500
    height: int = 300


class SysPath(BaseModel):
    path: str = None
    view: bool = True
    edit: bool = True


class SysPaths(BaseModel):
    notepad: SysPath = SysPath()
    vs_code: SysPath = SysPath()
    chrome: SysPath = SysPath()


class Group(BaseModel):
    name: Optional[str] = None
    pages: List[Tree] = []
    last_page_pinned_path: Optional[str] = None
    favorites: Favorites = Favorites()
    splitter_sizes: Optional[List[int]] = None

    def add_page(self, pinned_path: str = None) -> Tree:
        tree = Tree(pinned_path=pinned_path)
        self.pages.append(tree)
        return tree

    def get_page_by_pinned_path(self, pinned_path: str) -> Optional[Tree]:
        pages = [page for page in self.pages if page.pinned_path == pinned_path]
        return pages[0] if pages else None

    def remove_page(self, page: Tree):
        if page in self.pages:
            self.pages.remove(page)
        else:
            raise ValueError(f"Cannot remove\n{page}\nfrom pages\n{self.pages}")
        logger.debug(f"Page removed {page}")


class App(BaseModel):
    name: str = APP_NAME
    win_state: WindowState = WindowState()
    sys_paths: Optional[SysPaths] = SysPaths()
    search_win_state: SearchWindowState = SearchWindowState()
    last_group: Optional[str] = None
    groups: List[Group] = []

    def get_group_by_name(self, name: str):
        lookup = [group for group in self.groups if group.name == name]
        if not lookup or len(lookup) > 1:
            raise ValueError(f"Cannot find group by name {name} {lookup}")
        return lookup[0]

    def remove_group(self, group: Group):
        self.groups.remove(group)
