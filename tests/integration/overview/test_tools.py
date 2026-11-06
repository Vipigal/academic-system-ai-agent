from decimal import Decimal

from api.application.overview.dto.pending import (
    AttentionItemDto,
    CheckSituation,
    PendingArea,
    PendingItemsDto,
)
from api.application.shared.tool_result import ToolResult, ToolStatus
from api.persistence.core.database import Database
from tests.integration.overview import harness as overview_harness
from tests.integration.support.sql_oracle import SqlOracle

CR01_PERSON = "3002626"
CR01_CONTRACT = "CT00012318"
CLEAN_PERSON = "3000014"
ONLINE_PERSON = "3000009"

INVOICES_IN_WINDOW = (
    "SELECT duedate || ':' || netamountcents FROM finance.invoice WHERE contractid = :contract "
    "AND status IN ('OPEN', 'PARTIAL') AND duedate BETWEEN '2026-10-31' AND '2026-11-30'"
)
PROTOCOLS_IN_PROGRESS = (
    "SELECT protocol FROM secretary.protocol WHERE stu_id = '181820' "
    "AND demand_status NOT IN ('Resolved', 'Cancelled')"
)
LOW_ATTENDANCE = (
    "SELECT attendance_pct FROM sag.student_class WHERE student_id = '181820' "
    "AND brand = 'UniSaoPaulo' AND result = 'IN_PROGRESS' AND attendance_pct::numeric < 75"
)
OVERDUE_INVOICES = (
    "SELECT count(*) FROM finance.invoice WHERE contractid = :contract AND status = 'OVERDUE'"
)
ACTIVE_STATUS = (
    "SELECT enrollment_status FROM sag.enrollment "
    "WHERE brand = 'UniSaoPaulo' AND student_id = '181820'"
)


def pending(result: ToolResult[PendingItemsDto]) -> PendingItemsDto:
    assert result.data is not None
    return result.data


def attention_of(data: PendingItemsDto, area: PendingArea) -> list[AttentionItemDto]:
    return [item for item in data.attention if item.area is area]


async def cr01(database: Database) -> ToolResult[PendingItemsDto]:
    tools = await overview_harness.tools_for(database, CR01_PERSON)
    return await tools.get_pending_items()


async def test_cr01_enrollment_and_debt_match_the_database(database: Database) -> None:
    oracle = SqlOracle()
    data = pending(await cr01(database))

    assert await oracle.values(ACTIVE_STATUS) == {"ACTIVE"}
    assert await oracle.count(OVERDUE_INVOICES, contract=CR01_CONTRACT) == 0
    assert not attention_of(data, PendingArea.ENROLLMENT)
    assert not attention_of(data, PendingArea.DEBT)


async def test_cr01_upcoming_invoices_match_the_database(database: Database) -> None:
    data = pending(await cr01(database))

    invoices = {
        f"{item.detail['due_date']}:{int(Decimal(item.detail['amount_reais']) * 100)}"
        for item in attention_of(data, PendingArea.UPCOMING_INVOICES)
    }

    assert invoices == await SqlOracle().values(INVOICES_IN_WINDOW, contract=CR01_CONTRACT)
    assert invoices == {"2026-11-01:2000", "2026-11-10:148792"}


async def test_cr01_protocols_in_progress_match_the_database(database: Database) -> None:
    data = pending(await cr01(database))

    found = {item.reference for item in attention_of(data, PendingArea.PROTOCOLS)}

    assert found == await SqlOracle().values(PROTOCOLS_IN_PROGRESS)
    assert found == {"20260024674"}


async def test_cr01_attendance_below_75_matches_the_database(database: Database) -> None:
    data = pending(await cr01(database))

    attendance = attention_of(data, PendingArea.ATTENDANCE)

    assert [Decimal(item.detail["attendance_pct"]) for item in attendance] == [
        Decimal(value) for value in await SqlOracle().values(LOW_ATTENDANCE)
    ]
    assert [(item.reference, item.detail["subject"]) for item in attendance] == [
        ("DIR0403", "ADMINISTRATIVE LAW I")
    ]


async def test_cr01_totals_count_each_area_and_the_status_is_ok(database: Database) -> None:
    result = await cr01(database)

    assert result.status is ToolStatus.OK
    assert result.totals == {
        "matricula": 0,
        "divida": 0,
        "vencimentos": 2,
        "protocolo": 1,
        "frequencia": 1,
        "prova_online": len(attention_of(pending(result), PendingArea.ONLINE_EXAMS)),
    }


async def test_student_without_pending_items_still_lists_what_was_checked(
    database: Database,
) -> None:
    tools = await overview_harness.tools_for(database, CLEAN_PERSON)

    result = await tools.get_pending_items()
    data = pending(result)

    assert result.status is ToolStatus.OK
    assert data.attention == ()
    assert {item.area for item in data.checked} == set(PendingArea)
    assert {item.situation for item in data.checked} == {CheckSituation.OK}
    assert set(result.totals.values()) == {0}


async def test_attendance_caveat_comes_from_the_composed_service(database: Database) -> None:
    tools = await overview_harness.tools_for(database, ONLINE_PERSON)

    result = await tools.get_pending_items()

    assert {caveat.ontology for caveat in result.caveats} == {"frequencia"}
