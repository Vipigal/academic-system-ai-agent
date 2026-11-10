from api.application.protocol.queries import ProtocolQueries
from api.application.protocol.source import ProtocolSource
from api.application.shared.page import FIRST_PAGE
from api.application.shared.tool_result import ToolStatus
from evals.fixed_clock import FixedClock
from tests.unit.protocol.proposal_fakes import FakeAcademic
from tests.unit.protocol.protocol_fakes import InMemoryProtocols, NoFees

QUERIES = ProtocolQueries(
    ProtocolSource(InMemoryProtocols(), NoFees(), FakeAcademic(), FixedClock())
)


async def test_list_protocols_finds_the_review_by_its_portuguese_name() -> None:
    result = await QUERIES.list_protocols(None, "revisão de nota", None, FIRST_PAGE)

    assert result.data is not None
    assert [item.number for item in result.data] == ["20260013930"]
    assert result.data[0].service.title == "Revisão de nota"


async def test_list_protocols_still_finds_the_service_by_its_source_name() -> None:
    result = await QUERIES.list_protocols(None, "Grade Review", None, FIRST_PAGE)

    assert result.data is not None
    assert [item.number for item in result.data] == ["20260013930"]


async def test_list_services_shows_title_and_effect() -> None:
    result = await QUERIES.list_services(None)

    assert result.data is not None
    review = result.data[0]
    assert (review.code, review.title, review.available) == (
        "ACA-020",
        "Revisão de nota",
        True,
    )
    assert review.effect == "Pede à secretaria a revisão de uma nota."


async def test_a_service_outside_the_catalog_is_listed_closed() -> None:
    result = await QUERIES.list_services(None)

    assert result.data is not None
    unknown = result.data[2]
    assert (unknown.code, unknown.title, unknown.effect, unknown.available) == (
        "XYZ-999",
        None,
        None,
        False,
    )


async def test_a_portuguese_name_of_a_service_without_protocol_is_not_found() -> None:
    result = await QUERIES.list_protocols(None, "reclamação", None, FIRST_PAGE)

    assert result.status is ToolStatus.NOT_FOUND
