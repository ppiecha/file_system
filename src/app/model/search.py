from __future__ import annotations

import operator
import re
from enum import Enum, auto
from itertools import accumulate
from typing import Sequence, Iterator, Optional, List, Tuple, Dict

from chardet.universaldetector import UniversalDetector

from pydantic import BaseModel

from src.app.utils.path_util import extract_folders, path_caption


def format_keyword(keyword: str) -> str:
    return f"""<span style="background-color:transparent;color:gold">{keyword}</span>"""


def format_path(path: str) -> str:
    return f"""<span style="background-color:transparent;color:aqua">{path}</span>"""


def format_file_name(file_name: str) -> str:
    return f"""<span style="background-color:transparent;color:LightBlue">{file_name} </span>"""


def format_directory(directory: str) -> str:
    return f"""<b style="background-color:transparent;color:Gray">{directory}</b>"""


def format_error(file_name: str, error: str) -> str:
    return f"""{format_file_name(file_name)}<br>{error}"""


class SearchConfig(BaseModel):
    keywords: List[str] = []
    name_filters: List[str] = [
        "*.sql;*.pks;*.pkb;*.py;*.txt;*.xml",
        "*",
        "*.*",
        "*.py",
        "*.sql;*.pks;*.pkb",
        "*.xml",
    ]
    paths: List[str] = []
    excluded_dirs: List[str] = [
        "venv;__pycache__",
    ]


class SearchParam(BaseModel):
    keyword: Optional[str] = None
    path: Optional[str] = None
    name_filters: Optional[Sequence[str]] = []
    excluded_dirs: List[str] = []
    ignore_case: bool = True
    whole_words: bool = False
    reg_exp: bool = False
    subdirectories: bool = True

    def as_html(self) -> str:
        def search_type() -> str:
            if self.keyword:
                return format_keyword(keyword=self.keyword)
            return "for files and folders"

        return " ".join(
            [
                "Result(s) of searching",
                search_type(),
                "in",
                format_path(path=self.path),
                f"using filters {self.name_filters}",
            ]
        )


Range = Tuple[int, int]


class LineHit(BaseModel):
    line_range: Range
    line_number: int
    line_text: str
    hit_range: Range
    line_hit_range: Range
    file_name: str

    def column_number(self) -> int:
        return self.line_hit_range[0] + 1

    def as_html(self):
        line_number = f"""<span style="background-color:transparent;color:Gray">line {self.line_number}: </span>"""
        text_before = self.line_text[0 : self.line_hit_range[0]]
        text_before = f"""<span style="background-color:transparent">{text_before}</span >"""
        keyword = self.line_text[self.line_hit_range[0] : self.line_hit_range[1]]
        keyword = format_keyword(keyword=keyword)
        text_after = self.line_text[self.line_hit_range[1] :]
        text_after = f"""<span style="background-color:transparent">{text_after}</span>"""
        text = "".join([line_number, text_before, keyword, text_after])
        return f"<pre><code>{text}</code></pre>"


detector = UniversalDetector()


def file_encoding(file_name: str) -> str:
    detector.reset()
    for line in open(file_name, "rb"):
        detector.feed(line)
        if detector.done:
            break
    detector.close()
    return detector.result["encoding"]


def open_file(file_name: str) -> List[str] | str:
    # file_encoding(file_name=file_name)
    try:
        with open(file_name, "r", encoding="utf-8") as file:
            return file.readlines()
    except (UnicodeDecodeError, PermissionError, OSError) as e:
        return str(e)


LineRangeMap = Dict[Tuple[int, int], int]


def line_range_map(lines: List[str]) -> LineRangeMap:
    line_ends = list(accumulate([len(line) for line in lines], operator.add))
    current = 0
    ranges = {}
    for index, line_end in enumerate(line_ends):
        ranges[(current, line_end - 1)] = index
        current = line_end
    return ranges


def line_hit(match: re.Match, lines: List[str], line_map: LineRangeMap, file_name: str) -> LineHit:
    if match is None or len(match.regs) != 1:
        raise ValueError(f"Match is empty or contains not exactly one tuple {match}")
    hit_range = match.regs[0]
    if not lines:
        raise ValueError(f"Lines is None or empty {lines}")
    line_ranges = [
        (start_num, stop_num, line_num)
        for (start_num, stop_num), line_num in line_map.items()
        if start_num <= hit_range[0] <= stop_num
    ]
    if len(line_ranges) != 1:
        raise ValueError(f"Expecting exactly one line range {match} {line_map} {line_ranges}")
    line_range = line_ranges[0]
    line_number = line_range[2]
    line_range = (line_range[0], line_range[1])
    line_text = lines[line_number]
    line_hit_range = (hit_range[0] - line_range[0], hit_range[1] - line_range[0])
    return LineHit(
        line_range=line_range,
        line_number=line_number + 1,
        line_text=line_text.rstrip("\n"),
        hit_range=hit_range,
        line_hit_range=line_hit_range,
        file_name=file_name,
    )


class FileSearchResult(BaseModel):
    keyword: Optional[str] = None
    file_name: str
    is_dir: bool
    error: Optional[str] = None
    hits: Optional[List[re.Match]] = None

    class Config:
        arbitrary_types_allowed = True

    def hit_iter(self) -> Iterator[LineHit]:
        if self.hits is None:
            return ()
        lines = open_file(file_name=self.file_name)
        line_map = line_range_map(lines=lines)
        return (line_hit(match=match, lines=lines, line_map=line_map, file_name=self.file_name) for match in self.hits)

    def file_caption(self) -> str:
        pass

    def file_directory(self) -> str:
        return path_caption(path=extract_folders([self.file_name])[0])

    def as_html(self) -> str:
        if self.error:
            return format_error(file_name=self.file_name, error=self.error)
        return format_file_name(file_name=self.file_name)


class FileSearchResultList(BaseModel):
    __root__: List[FileSearchResult] = []

    def __iter__(self) -> Iterator[FileSearchResult]:
        return iter(self.__root__)

    def __getitem__(self, item) -> FileSearchResult:
        return self.__root__[item]

    def __len__(self):
        return len(self.__root__)


class SearchState(Enum):
    READY = auto()
    RUNNING = auto()
    CANCELLED = auto()
    COMPLETED = auto()
