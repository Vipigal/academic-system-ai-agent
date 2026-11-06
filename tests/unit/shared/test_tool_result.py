from datetime import date
from decimal import Decimal

import pytest
from pydantic import BaseModel, ConfigDict

from api.application.shared.page import PageRequest
from api.application.shared.tool_input_error import ToolInputError
from api.application.shared.tool_result import (
    MAX_CANDIDATES,
    Candidate,
    Caveat,
    Coverage,
    DataState,
    StatedValue,
    ToolResult,
    ToolStatus,
)
from api.domain.ontology.academic_performance import CRITERIO_DE_APROVACAO
from api.domain.ontology.finance_charges import DIVIDA


class SubjectRecordDto(BaseModel):
    model_config = ConfigDict(frozen=True)

    code: str
    second_exam: StatedValue[Decimal]


def test_listing_serializes_as_the_documented_envelope() -> None:
    page = PageRequest(limit=2).paginate(("a", "b", "c"))
    caveat = Caveat.from_ontology(CRITERIO_DE_APROVACAO)
    coverage = Coverage(from_date=date(2023, 1, 15), note="O ambiente virtual começa nesta data.")

    result = ToolResult.listing(
        page, totals={"net": Decimal("41234.50")}, caveats=(caveat,), coverage=coverage
    )

    assert result.model_dump(mode="json") == {
        "status": "ok",
        "data": ["a", "b"],
        "page": {"offset": 0, "limit": 2, "total": 3, "next_offset": 2},
        "totals": {"net": "41234.50"},
        "caveats": [{"ontology": "criterio_de_aprovacao", "text": CRITERIO_DE_APROVACAO.caveat}],
        "coverage": {"from": "2023-01-15", "note": "O ambiente virtual começa nesta data."},
        "candidates": [],
    }


def test_listing_of_an_empty_set_is_empty_with_a_page() -> None:
    no_items: tuple[str, ...] = ()

    result = ToolResult.listing(PageRequest().paginate(no_items))

    assert result.status is ToolStatus.EMPTY
    assert result.data == []
    assert result.page is not None
    assert result.page.total == 0


def test_listing_past_the_end_is_still_ok_because_the_set_has_items() -> None:
    result = ToolResult.listing(PageRequest(offset=10).paginate(("a", "b")))

    assert result.status is ToolStatus.OK
    assert result.data == []


def test_single_result_omits_page_and_coverage() -> None:
    dumped = ToolResult.ok("summary").model_dump(mode="json")

    assert dumped == {
        "status": "ok",
        "data": "summary",
        "totals": {},
        "caveats": [],
        "candidates": [],
    }


def test_items_without_pagination_are_ok_and_keep_totals_caveats_and_coverage() -> None:
    caveat = Caveat.from_ontology(CRITERIO_DE_APROVACAO)
    coverage = Coverage(from_date=date(2023, 2, 1), note="Sem registros antes desta data.")

    result = ToolResult.items(("a", "b"), totals={"n": 2}, caveats=(caveat,), coverage=coverage)

    assert result.model_dump(mode="json") == {
        "status": "ok",
        "data": ["a", "b"],
        "totals": {"n": 2},
        "caveats": [{"ontology": "criterio_de_aprovacao", "text": CRITERIO_DE_APROVACAO.caveat}],
        "coverage": {"from": "2023-02-01", "note": "Sem registros antes desta data."},
        "candidates": [],
    }


def test_items_of_an_empty_sequence_is_empty_with_a_list() -> None:
    no_items: tuple[str, ...] = ()
    caveat = Caveat.from_ontology(CRITERIO_DE_APROVACAO)

    result = ToolResult.items(no_items, caveats=(caveat,))

    assert result.status is ToolStatus.EMPTY
    assert result.data == []
    assert result.page is None
    assert result.caveats == (caveat,)


def test_ok_carries_totals() -> None:
    result = ToolResult.ok("summary", totals={"debt": Decimal("10.50")})

    assert result.model_dump(mode="json")["totals"] == {"debt": "10.50"}


def test_not_found_lists_the_student_candidates() -> None:
    candidate = Candidate(code="ADS0102", name="ALGORITHMS AND PROGRAMMING II")

    dumped = ToolResult[str].not_found((candidate,)).model_dump(mode="json")

    assert dumped["status"] == "not_found"
    assert dumped["data"] is None
    assert dumped["candidates"] == [{"code": "ADS0102", "name": "ALGORITHMS AND PROGRAMMING II"}]


def test_ambiguous_lists_the_candidates() -> None:
    candidate = Candidate(code="UNI:181820", name="Administração")

    result = ToolResult[str].ambiguous((candidate,))

    assert result.status is ToolStatus.AMBIGUOUS
    assert result.candidates == (candidate,)


def test_refused_explains_itself_through_data_and_caveats() -> None:
    caveat = Caveat.from_ontology(CRITERIO_DE_APROVACAO)

    result = ToolResult.refused("duplicated", caveats=(caveat,))

    assert result.status is ToolStatus.REFUSED
    assert result.data == "duplicated"
    assert result.caveats == (caveat,)


def test_caveat_takes_key_and_text_from_the_ontology_and_nothing_else() -> None:
    dumped = Caveat.from_ontology(CRITERIO_DE_APROVACAO).model_dump(mode="json")

    assert dumped == {
        "ontology": CRITERIO_DE_APROVACAO.key,
        "text": CRITERIO_DE_APROVACAO.caveat,
    }


def test_caveat_refuses_an_ontology_without_a_caveat() -> None:
    assert DIVIDA.caveat is None

    with pytest.raises(ValueError, match="divida"):
        Caveat.from_ontology(DIVIDA)


def test_recorded_value_keeps_zero_distinct_from_missing() -> None:
    dumped = StatedValue.recorded(Decimal(0)).model_dump(mode="json")

    assert dumped == {"state": "recorded", "value": "0"}


@pytest.mark.parametrize(
    ("value", "state"),
    [
        (StatedValue[Decimal].not_yet(), "not_yet"),
        (StatedValue[Decimal].not_recorded(), "not_recorded"),
    ],
)
def test_missing_value_says_why_and_carries_no_value(
    value: StatedValue[Decimal], state: str
) -> None:
    assert value.value is None
    assert value.model_dump(mode="json") == {"state": state}


def test_stated_value_fits_a_typed_dto_field() -> None:
    recorded = SubjectRecordDto(code="ADS0102", second_exam=StatedValue.recorded(Decimal("7.5")))
    pending = SubjectRecordDto(code="ADS0103", second_exam=StatedValue[Decimal].not_yet())

    assert recorded.second_exam.state is DataState.RECORDED
    assert recorded.second_exam.value == Decimal("7.5")
    assert pending.model_dump(mode="json") == {
        "code": "ADS0103",
        "second_exam": {"state": "not_yet"},
    }


def test_dto_list_serializes_inside_the_envelope() -> None:
    record = SubjectRecordDto(code="ADS0102", second_exam=StatedValue.recorded(Decimal("7.5")))

    dumped = ToolResult.listing(PageRequest().paginate((record,))).model_dump(mode="json")

    assert dumped["data"] == [
        {"code": "ADS0102", "second_exam": {"state": "recorded", "value": "7.5"}}
    ]


def test_candidates_are_capped_for_not_found_and_ambiguous() -> None:
    many = tuple(Candidate(code=str(number), name="x") for number in range(MAX_CANDIDATES + 10))
    for result in (ToolResult[str].not_found(many), ToolResult[str].ambiguous(many)):
        assert result.candidates == many[:MAX_CANDIDATES]


def test_the_explanation_appears_only_when_there_is_one() -> None:
    result = ToolResult[str](status=ToolStatus.INVALID, explanation="O parâmetro veio errado.")

    assert result.model_dump(mode="json") == {
        "status": "invalid",
        "data": None,
        "totals": {},
        "caveats": [],
        "candidates": [],
        "explanation": "O parâmetro veio errado.",
    }
    assert ToolStatus.ERROR.value == "error"
    assert "explanation" not in ToolResult.ok("x").model_dump(mode="json")


def test_tool_input_error_carries_the_paragraph() -> None:
    assert ToolInputError("Use o formato AAAA-MM.").explanation == "Use o formato AAAA-MM."


def test_client_only_never_leaves_through_the_default_serialization() -> None:
    result = ToolResult.ok("proposta").with_client_only({"token": "segredo"})

    assert result.client_only == {"token": "segredo"}
    assert "segredo" not in result.model_dump_json()
    assert "client_only" not in result.model_dump(mode="json")
    assert "segredo" not in repr(result)
