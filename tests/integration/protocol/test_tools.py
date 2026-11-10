from datetime import date, datetime
from decimal import Decimal

from api.application.agent.tool_arguments import BoundedPage
from api.application.shared.tool_result import ToolStatus
from api.domain.finance.invoice import InvoiceStatus
from api.domain.protocol.status import DeadlineSituation, ProtocolStage, ProtocolStatus, Resolution
from api.persistence.core.column_types import BRASILIA
from api.persistence.core.database import Database
from tests.integration.protocol import harness, support
from tests.integration.support.sql_oracle import SqlOracle


async def test_pr01_protocol_in_analysis_is_within_deadline(database: Database) -> None:
    tools = await harness.tools_for(database, support.ONLINE_SAO_PAULO_PERSON)

    protocol = support.protocol_of(await tools.get_protocol("PRT-2026/0024630"))

    assert (protocol.number, protocol.status, protocol.enrollment) == (
        "20260024630",
        ProtocolStatus.IN_ANALYSIS,
        "UniSaoPaulo_EAD:012831",
    )
    assert protocol.status_since == datetime(2026, 10, 30, 8, 40, 7, tzinfo=BRASILIA)
    assert (protocol.deadline.due_at, protocol.deadline.situation) == (
        datetime(2026, 11, 1, 14, 50, 59, tzinfo=BRASILIA),
        DeadlineSituation.WITHIN_DEADLINE,
    )


async def test_pr01_the_fee_invoice_is_open_and_unpaid(database: Database) -> None:
    tools = await harness.tools_for(database, support.ONLINE_SAO_PAULO_PERSON)

    fee = support.protocol_of(await tools.get_protocol("PRT-2026/0024630")).fee

    assert fee is not None
    assert fee.amount_reais == 20
    assert fee.invoice is not None
    assert (fee.invoice.due_date, fee.invoice.status, fee.invoice.is_paid) == (
        date(2026, 11, 1),
        InvoiceStatus.OPEN,
        False,
    )


async def test_the_number_without_prefix_finds_the_same_protocol(database: Database) -> None:
    tools = await harness.tools_for(database, support.ONLINE_SAO_PAULO_PERSON)

    result = await tools.get_protocol("20260024630")

    assert result.status is ToolStatus.OK


async def test_pr02_protocol_without_student_id_is_listed_in_progress(database: Database) -> None:
    tools = await harness.tools_for(database, support.LITORAL_PERSON)

    result = await tools.list_protocols(status=ProtocolStage.IN_PROGRESS)

    [found] = support.rows(result)
    assert (found.number, found.enrollment) == ("20260024837", None)
    assert found.deadline.due_at == datetime(2026, 11, 5, 13, 13, 20, tzinfo=BRASILIA)
    assert dict(result.totals) == {"in_progress": 1, "overdue": 0}


async def test_pr02_fee_of_the_listed_protocol(database: Database) -> None:
    tools = await harness.tools_for(database, support.LITORAL_PERSON)

    [found] = support.rows(await tools.list_protocols(status=ProtocolStage.IN_PROGRESS))

    assert found.fee is not None
    assert found.fee.invoice is not None
    assert (found.fee.amount_reais, found.fee.invoice.due_date) == (Decimal(30), date(2026, 11, 3))


async def test_pr02_empty_list_is_the_normal_answer(database: Database) -> None:
    tools = await harness.tools_for(database, support.SAO_PAULO_PERSON)
    oracle = SqlOracle()

    result = await tools.list_protocols(status=ProtocolStage.IN_PROGRESS)

    assert (result.status, result.data) == (ToolStatus.EMPTY, [])
    assert (
        await oracle.count(
            "SELECT count(*) FROM secretary.protocol WHERE stu_id = '181722' "
            "AND demand_status IN ('Open', 'In Analysis')"
        )
        == 0
    )


async def test_pr03_denied_review_has_no_recorded_reason(database: Database) -> None:
    tools = await harness.tools_for(database, support.ATLANTICO_PERSON)
    oracle = SqlOracle()

    result = await tools.get_protocol("20260013930")

    assert result.data is not None
    assert (result.data.protocol.status, result.data.protocol.resolution) == (
        ProtocolStatus.RESOLVED,
        Resolution.DENIED,
    )
    assert len(result.data.messages) == await oracle.count(
        "SELECT count(*) FROM secretary.protocol_interaction "
        "WHERE protocol = '20260013930' AND is_internal_note = 'False'"
    )


async def test_pr04_certificate_with_its_validation_code(database: Database) -> None:
    tools = await harness.tools_for(database, support.ARAUCARIA_ONLINE_PERSON)
    oracle = SqlOracle()

    result = await tools.get_protocol("20260024348")

    assert result.data is not None
    documents = result.data.protocol.documents
    assert {item.validation_code for item in documents} == await oracle.values(
        "SELECT validation_code FROM secretary.issued_document WHERE protocol = '20260024348'"
    )
    assert len(documents) == 1


async def test_pr04_diploma_request_has_two_documents(database: Database) -> None:
    tools = await harness.tools_for(database, support.DIPLOMA_PERSON)

    result = await tools.get_protocol("20230000406")

    assert result.data is not None
    assert len(result.data.protocol.documents) == 2


async def test_cr08_resolved_second_call_with_the_fee_overdue(database: Database) -> None:
    tools = await harness.tools_for(database, support.UNPAID_FEE_PERSON)

    protocol = support.protocol_of(await tools.get_protocol("20260022332"))

    assert protocol.status is ProtocolStatus.RESOLVED
    assert protocol.fee is not None
    assert protocol.fee.invoice is not None
    assert (protocol.fee.amount_reais, protocol.fee.invoice.invoice_id) == (Decimal(45), "7077556")
    assert (protocol.fee.invoice.status, protocol.fee.invoice.is_paid) == (
        InvoiceStatus.OVERDUE,
        False,
    )


async def test_resolved_second_call_without_an_invoice_has_no_invoice(database: Database) -> None:
    tools = await harness.tools_for(database, support.NO_FEE_INVOICE_PERSON)

    fee = support.protocol_of(await tools.get_protocol("20260021621")).fee

    assert fee is not None
    assert fee.invoice is None


async def test_pr09_protocol_opened_by_the_guardian_is_visible_without_who_opened(
    database: Database,
) -> None:
    tools = await harness.tools_for(database, support.GUARDIAN_PERSON)
    oracle = SqlOracle()

    result = await tools.get_protocol("20260024432")

    assert result.data is not None
    assert result.data.protocol.opened_by.value == "guardian"
    dumped = result.model_dump_json()
    for secret in await oracle.values(
        "SELECT requester_name FROM secretary.protocol WHERE protocol = '20260024432' "
        "UNION SELECT requester_cpf FROM secretary.protocol WHERE protocol = '20260024432'"
    ):
        assert secret not in dumped


async def test_pr09_guardian_protocol_without_proof_is_not_found(database: Database) -> None:
    tools = await harness.tools_for(database, support.GUARDIAN_PERSON)

    result = await tools.get_protocol("20260024792")

    assert (result.status, result.data) == (ToolStatus.NOT_FOUND, None)
    assert "20260024792" not in support.candidate_codes(result)
    assert "20260024432" in support.candidate_codes(result)


async def test_re05_no_internal_note_and_no_analyst(database: Database) -> None:
    tools = await harness.tools_for(database, support.INTERNAL_NOTES_PERSON)
    oracle = SqlOracle()

    result = await tools.get_protocol("20260000513")

    assert result.data is not None
    assert len(result.data.messages) == await oracle.count(
        "SELECT count(*) FROM secretary.protocol_interaction "
        "WHERE protocol = '20260000513' AND is_internal_note = 'False'"
    )
    dumped = result.model_dump_json()
    leaked = await oracle.values(
        "SELECT message FROM secretary.protocol_interaction "
        "WHERE protocol = '20260000513' AND is_internal_note = 'True' "
        "UNION SELECT author FROM secretary.protocol_interaction WHERE protocol = '20260000513' "
        "AND author_type = 'Analyst' "
        "UNION SELECT changed_by FROM secretary.protocol_status_history "
        "WHERE protocol = '20260000513' AND changed_by <> 'system' "
        "UNION SELECT demand_analyst FROM secretary.protocol WHERE protocol = '20260000513'"
    )
    assert leaked
    assert not any(value in dumped for value in leaked)


async def test_list_filters_by_service_name_and_period(database: Database) -> None:
    tools = await harness.tools_for(database, support.ONLINE_SAO_PAULO_PERSON)

    by_name = support.rows(await tools.list_protocols(service="printed transcript"))
    in_month = support.rows(await tools.list_protocols(period="2026-10"))
    bad_month = await tools.list_protocols(period="2026-1")

    assert {item.service.code for item in by_name} == {"DOC-002"}
    assert {item.number for item in in_month} == {"20260024630", "20260023525"}
    assert {item.opened_at.month for item in in_month} == {10}
    assert bad_month.status is ToolStatus.EMPTY


async def test_list_unknown_service_is_not_found_with_the_students_services(
    database: Database,
) -> None:
    tools = await harness.tools_for(database, support.ONLINE_SAO_PAULO_PERSON)

    result = await tools.list_protocols(service="bolsa")

    assert result.status is ToolStatus.NOT_FOUND
    assert "DOC-002" in support.candidate_codes(result)
    assert "FIN-032" not in support.candidate_codes(result)


async def test_list_is_paginated_newest_first(database: Database) -> None:
    tools = await harness.tools_for(database, support.ONLINE_SAO_PAULO_PERSON)

    first = await tools.list_protocols(page=BoundedPage(limit=1))
    everything = support.rows(await tools.list_protocols(page=BoundedPage(limit=100)))

    assert first.page is not None
    assert first.page.total == len(everything)
    assert first.data == everything[:1]
    opened = [item.opened_at for item in everything]
    assert opened == sorted(opened, reverse=True)
