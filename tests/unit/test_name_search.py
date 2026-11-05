from api.application.dto.tool_result import Candidate
from api.application.name_search import NameSearch

FIRST = Candidate(code="ADS0102", name="ALGORITHMS AND PROGRAMMING I")
SECOND = Candidate(code="ADS0404", name="ALGORITHMS AND PROGRAMMING II")
CANDIDATES = (SECOND, FIRST, SECOND)


def test_no_query_keeps_every_candidate_once_and_in_code_order() -> None:
    match = NameSearch.search(None, CANDIDATES)

    assert match.candidates == (FIRST, SECOND)
    assert match.matched == (FIRST, SECOND)
    assert not match.missed


def test_ignores_case_accent_and_extra_spaces() -> None:
    accented = Candidate(code="X1", name="INTRODUÇÃO  À LÓGICA")

    assert NameSearch.search("introducao a logica", (accented,)).matched == (accented,)


def test_partial_name_matches_several() -> None:
    match = NameSearch.search("algorithms", CANDIDATES)

    assert match.matched == (FIRST, SECOND)
    assert match.is_ambiguous


def test_exact_name_wins_over_a_longer_name_that_contains_it() -> None:
    assert NameSearch.search("algorithms and programming i", CANDIDATES).matched == (FIRST,)


def test_code_matches() -> None:
    assert NameSearch.search("ads0404", CANDIDATES).codes == {"ADS0404"}


def test_no_match_reports_a_miss_with_every_candidate() -> None:
    match = NameSearch.search("Programação II", CANDIDATES)

    assert match.missed
    assert match.candidates == (FIRST, SECOND)


def test_blank_query_matches_nothing() -> None:
    assert NameSearch.search("  ", CANDIDATES).missed
