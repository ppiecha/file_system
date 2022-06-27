import operator
import re
from itertools import accumulate
from typing import Sequence, Iterator, Optional, List, Tuple, Dict

from pydantic import BaseModel


class SearchParam(BaseModel):
    keyword: Optional[str] = None
    path: Optional[str] = None
    name_filters: Optional[Sequence[str]] = []
    excluded_dirs: List[str] = []
    ignore_case: bool = True
    whole_words: bool = False
    reg_exp: bool = False
    subdirectories: bool = True


Range = Tuple[int, int]


class LineHit(BaseModel):
    line_range: Range
    line_number: int
    line_text: str
    hit_range: Range
    line_hit_range: Range

    def as_html(self):
        line_number = f"""<span style="background-color:transparent;color:Gray">Line {self.line_number}:</span>"""
        text_before = self.line_text[0 : self.line_hit_range[0]]
        text_before = f"""<span style="background-color:transparent">{text_before}</span >"""
        keyword = self.line_text[self.line_hit_range[0] : self.line_hit_range[1]]
        keyword = f"""<span style="background-color:transparent;color:#FFFF00">{keyword}</span>"""
        text_after = self.line_text[self.line_hit_range[1] :]
        text_after = f"""<span style="background-color:transparent">{text_after}</span>"""
        return "".join([line_number, text_before, keyword, text_after])


def open_file(file_name: str) -> List[str] | str:
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


def line_hit(match: re.Match, lines: List[str], line_map: LineRangeMap) -> LineHit:
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
        raise ValueError(f"Expecting exactly one line range {match} {line_map}")
    line_range = line_ranges[0]
    line_number = line_range[2]
    line_range = (line_range[0], line_range[1])
    line_text = lines[line_number]
    line_hit_range = (hit_range[0] - line_range[0], hit_range[1] - line_range[0])
    return LineHit(
        line_range=line_range,
        line_number=line_number,
        line_text=line_text,
        hit_range=hit_range,
        line_hit_range=line_hit_range,
    )


class FileSearchResult(BaseModel):
    keyword: str
    file_name: str
    is_dir: bool
    error: Optional[str] = None
    hits: Optional[Iterator[re.Match]] = None

    class Config:
        arbitrary_types_allowed = True

    def hit_iter(self) -> Iterator[LineHit]:
        if self.hits is None:
            return ()
        lines = open_file(file_name=self.file_name)
        line_map = line_range_map(lines=lines)
        return (line_hit(match=match, lines=lines, line_map=line_map) for match in self.hits)

    def file_caption(self) -> str:
        pass

    def file_directory(self) -> str:
        pass

    def as_html(self):
        return f"""<span style="background-color:transparent;color:white" >{self.file_name}</span>"""
        # return f"""<b>{self.file_name}</b>"""
