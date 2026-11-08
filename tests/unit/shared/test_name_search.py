from api.application.shared.name_search import NameSearch
from api.application.shared.tool_result import Candidate

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


GRADE_REVIEW = Candidate(code="ACA-020", name="Grade Review")
COMPLAINT = Candidate(code="OUV-099", name="Complaint")
TITLES = {"ACA-020": "Revisão de nota", "OUV-099": "Reclamação na ouvidoria"}


def test_an_alias_of_the_code_matches_like_the_name() -> None:
    match = NameSearch.search("revisao de nota", (GRADE_REVIEW, COMPLAINT), TITLES)

    assert match.matched == (GRADE_REVIEW,)


def test_the_name_still_matches_when_there_is_an_alias() -> None:
    match = NameSearch.search("grade review", (GRADE_REVIEW, COMPLAINT), TITLES)

    assert match.matched == (GRADE_REVIEW,)


def test_a_partial_alias_matches() -> None:
    assert NameSearch.search("ouvidoria", (GRADE_REVIEW, COMPLAINT), TITLES).codes == {"OUV-099"}


def test_without_aliases_the_portuguese_name_misses() -> None:
    assert NameSearch.search("revisão de nota", (GRADE_REVIEW, COMPLAINT)).missed
