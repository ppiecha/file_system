import re
from typing import Iterator, List

from PySide2.QtCore import QDirIterator, QDir, QFileInfo

from src.app.model.search import FileSearchResult, SearchParam, open_file, SearchState
from src.app.utils.logger import get_console_logger

logger = get_console_logger(name=__name__)


def find_keyword(
    search_param: SearchParam,
    text: str,
    find_first: bool = False,
) -> Iterator[re.Match] | re.Match:
    flag = re.IGNORECASE if search_param.ignore_case else 0
    esc_word = search_param.keyword if search_param.reg_exp else re.escape(search_param.keyword)
    pattern = r"\b" + esc_word + r"\b" if search_param.whole_words else r"" + esc_word + r""
    if find_first:
        return re.search(pattern=pattern, string=text, flags=flag)
    return re.finditer(pattern=pattern, string=text, flags=flag)


def search_file(
    search_param: SearchParam, text_lines: List[str] | str, search_result: FileSearchResult
) -> FileSearchResult:
    def has_hits(data: str) -> bool:
        return find_keyword(search_param=search_param, text=data, find_first=True) is not None

    if isinstance(text_lines, str):
        search_result.error = text_lines
    else:
        text = "".join(text_lines)
        if has_hits(data=text):
            search_result.hits = find_keyword(search_param=search_param, text=text)
    return search_result


def search(
    search_param: SearchParam,
    filters: QDir.Filters = QDir.AllEntries | QDir.NoSymLinks | QDir.Dirs | QDir.NoDotAndDotDot | QDir.DirsFirst,
) -> Iterator[FileSearchResult]:
    flags = QDirIterator.Subdirectories if search_param.subdirectories else QDirIterator.NoIteratorFlags
    it = QDirIterator(search_param.path, search_param.name_filters, filters, flags)
    while it.hasNext():
        file_name = it.next()
        file_info = QFileInfo(file_name)
        search_result = FileSearchResult(
            keyword=search_param.keyword,
            file_name=file_name,
            is_dir=file_info.isDir(),
        )
        if not search_result.is_dir and search_param.keyword:
            text_lines = open_file(file_name=file_name)
            search_result = search_file(search_param=search_param, text_lines=text_lines, search_result=search_result)
        if search_result.error is not None or search_result.hits is not None or not search_param.keyword:
            yield search_result
        if search_result.error:
            logger.error(search_result.error)
