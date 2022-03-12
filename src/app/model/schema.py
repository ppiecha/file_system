from typing import Optional, List

from pydantic import BaseModel


class Tree(BaseModel):
    root_path: str
    current_path: Optional[str] = None
    visible_columns: List[int] = []
    hide_header: bool = True
    show_files: bool = True
    show_hidden: bool = False
    show_system: bool = False


class Navigator(BaseModel):
    left: List[Tree] = []
    right: List[Tree] = []
