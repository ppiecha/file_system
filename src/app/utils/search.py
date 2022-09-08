import logging
import re
from typing import Iterator, List, Union

from PySide2.QtCore import QDirIterator, QDir, QFileInfo

from src.app.model.search import FileSearchResult, SearchParam
from src.app.utils.logger import get_console_logger

logger = get_console_logger(name=__name__, log_level=logging.ERROR)


def find_keyword(
    search_param: SearchParam,
    text: str,
    find_first: bool = False,
) -> Union[Iterator[re.Match], re.Match]:
    flag = re.IGNORECASE if search_param.ignore_case else 0
    esc_word = search_param.keyword if search_param.reg_exp else re.escape(search_param.keyword)
    pattern = r"\b" + esc_word + r"\b" if search_param.whole_words else r"" + esc_word + r""
    if find_first:
        return re.search(pattern=pattern, string=text, flags=flag)
    return re.finditer(pattern=pattern, string=text, flags=flag)


def search_file(
    search_param: SearchParam, text_lines: Union[List[str], str], search_result: FileSearchResult
) -> FileSearchResult:
    def has_hits(data: str) -> bool:
        return find_keyword(search_param=search_param, text=data, find_first=True) is not None

    if isinstance(text_lines, str):
        search_result.error = text_lines
    else:
        text = "".join(text_lines)
        if has_hits(data=text):
            search_result.hits = list(find_keyword(search_param=search_param, text=text))
    return search_result


def is_in_excluded_dirs(file_info: QFileInfo, excluded_dirs: List[str]):
    path = file_info.fileName()
    if file_info.isFile():
        path = file_info.path()
    path_parts = path.split("/")
    for excluded_folder in excluded_dirs:
        if [part for part in path_parts if part.lower() == excluded_folder.lower()]:
            return True
    return False


def search(
    search_param: SearchParam,
    filters: QDir.Filters = QDir.AllEntries | QDir.NoSymLinks | QDir.Dirs | QDir.NoDotAndDotDot | QDir.DirsFirst,
) -> Iterator[FileSearchResult]:
    flags = QDirIterator.Subdirectories if search_param.subdirectories else QDirIterator.NoIteratorFlags
    it = QDirIterator(search_param.path, search_param.name_filters, filters, flags)
    while it.hasNext():
        file_name = it.next()
        file_info = QFileInfo(file_name)
        if is_in_excluded_dirs(file_info=file_info, excluded_dirs=search_param.excluded_dirs):
            continue
        yield FileSearchResult(
            keyword=search_param.keyword,
            file_name=file_name,
            is_dir=file_info.isDir(),
        )
