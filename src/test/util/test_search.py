import re
from typing import Iterator

from src.app.model.search import SearchParam, line_range_map
from src.app.utils.search import find_keyword, search

text1 = """flag = re.IGNORECASE if not case_sensitive else 0"""


def assert_keyword(keyword: str, text: str, hits: Iterator[re.Match], ignore_case: bool = True):
    for hit in hits:
        for reg in hit.regs:
            if ignore_case:
                assert text[reg[0] : reg[1]].lower() == keyword.lower()
            else:
                assert text[reg[0] : reg[1]] == keyword


def test_re_search():
    search_param = SearchParam()
    search_param.keyword = "re"
    search_param.ignore_case = True
    hits = find_keyword(search_param=search_param, text=text1)
    assert_keyword(keyword=search_param.keyword, text=text1, hits=hits, ignore_case=search_param.ignore_case)

    search_param.ignore_case = False
    hits = find_keyword(search_param=search_param, text=text1)
    assert_keyword(keyword=search_param.keyword, text=text1, hits=hits, ignore_case=search_param.ignore_case)

    search_param.keyword = "case"
    hits = find_keyword(search_param=search_param, text=text1)
    assert_keyword(keyword=search_param.keyword, text=text1, hits=hits, ignore_case=search_param.ignore_case)


text2 = """keyword: str, text: str, ignore_case: bool = True, whole_words: bool = False, reg_exp: bool = False
) -> Iterator[re.Match]:
    flag = re.IGNORECASE if ignore_case else 0
    esc_word = keyword if reg_exp else re.escape(keyword)
    pattern = r"\b" + esc_word + r"\b" if whole_words else r"" + esc_word + r""
    print("pattern", pattern)
    return re.finditer(pattern=pattern, string=text, flags=flag)"""


def test_re_search_multiline():
    search_param = SearchParam()
    search_param.keyword = "\b"
    search_param.ignore_case = True
    hits = find_keyword(search_param=search_param, text=text2)
    assert_keyword(keyword=search_param.keyword, text=text2, hits=hits, ignore_case=search_param.ignore_case)

    search_param.keyword = "str"
    search_param.ignore_case = True
    hits = find_keyword(search_param=search_param, text=text2)
    for hit in hits:
        print(hit)
    assert_keyword(keyword=search_param.keyword, text=text2, hits=hits, ignore_case=search_param.ignore_case)

    search_param.keyword = "False\n)"
    search_param.ignore_case = True
    hits = find_keyword(
        search_param=search_param,
        text=text2,
    )
    for hit in hits:
        print(hit)
    assert_keyword(keyword=search_param.keyword, text=text2, hits=hits, ignore_case=search_param.ignore_case)


def test_re_search_find_first():
    search_param = SearchParam()
    search_param.keyword = "str"
    search_param.ignore_case = True
    match = find_keyword(search_param=search_param, text=text2, find_first=True)
    print(match)
    assert match.regs == ((9, 12),)


def test_re_search_not_found():
    search_param = SearchParam()
    search_param.keyword = "cat"
    search_param.ignore_case = True
    match = find_keyword(search_param=search_param, text=text1, find_first=True)
    assert match is None
    hits = find_keyword(search_param=search_param, text=text1)
    assert len(list(hits)) == 0
    assert_keyword(keyword=search_param.keyword, text=text1, hits=hits, ignore_case=search_param.ignore_case)


def test_re_search_file_search():
    search_param = SearchParam(keyword="run_in_thread", path=r"C:/Users/piotr/_piotr_/__GIT__/Python/Navigator/util")
    search_results = search(search_param=search_param)
    for result in [search_result for search_result in search_results if search_result.error is None]:
        print(result)
        for line_hit in result.hit_iter():
            print(line_hit)
            print(line_hit.as_html())


def test_file_line_range():
    print(line_range_map(["aaa", "bb", "c"]))
    assert line_range_map(["aaa", "bb", "c"]) == {(0, 2): 0, (3, 4): 1, (5, 5): 2}
