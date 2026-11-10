from decimal import Decimal

import pytest

from api.application.agent.tools.protocol import ProtocolTools
from api.application.agent.tools.registry import ToolRegistry
from api.application.protocol.dto.proposal import ProtocolProposalDto, ProtocolRefusalDto
from api.application.shared.tool_result import ToolResult, ToolStatus
from api.domain.protocol.action import ProtocolAction
from api.domain.protocol.catalog import ServiceArea
from api.domain.protocol.proposal import RefusalReason
from api.persistence.core.database import Database
from tests.integration.protocol import harness, support
from tests.integration.support.sql_oracle import SqlOracle

SAO_PAULO = "UniSaoPaulo:181722"
LOCKED = "UniSaoPaulo:180882"
FREE_ACTIVE_SERVICES = (
    "SELECT count(*) FROM secretary.demand_type WHERE active = 'True' AND service_fee = 'R$ 0,00'"
)


async def test_the_four_tools_are_in_the_registry(tools: ProtocolTools) -> None:
    registered = {tool.definition.name for tool in ToolRegistry(tools).tools}

    assert registered == {"list_services", "list_protocols", "get_protocol", "propose_protocol"}


async def test_every_service_of_the_secretary_has_title_and_effect(tools: ProtocolTools) -> None:
    services = support.rows(await tools.list_services())

    assert [item.code for item in services if not (item.title and item.effect)] == []


async def test_du06_eighteen_services_fourteen_without_fee(tools: ProtocolTools) -> None:
    oracle = SqlOracle()

    services = support.rows(await tools.list_services())

    assert (len(services), sum(not item.fee_reais and item.active for item in services)) == (
        await oracle.count("SELECT count(*) FROM secretary.demand_type"),
        await oracle.count(FREE_ACTIVE_SERVICES),
    )
    assert {item.code for item in services if item.fee_reais} == {
        "ACA-021",
        "DOC-002",
        "DOC-003",
        "DOC-041",
    }
    second_call = next(item for item in services if item.code == "ACA-021")
    assert (second_call.fee_reais, second_call.sla_hours, second_call.name) == (
        Decimal(45),
        72,
        "Second-Call Exam",
    )
    assert await oracle.values(
        "SELECT service_fee || ' ' || sla_hours FROM secretary.demand_type "
        "WHERE demand_code = 'ACA-021'"
    ) == {"R$ 45,00 72"}


async def test_du06_area_filter(tools: ProtocolTools) -> None:
    documents = support.rows(await tools.list_services(ServiceArea.DOCUMENTS))

    assert {item.code for item in documents} == {
        "DOC-001",
        "DOC-002",
        "DOC-003",
        "DOC-040",
        "DOC-041",
    }


@pytest.fixture
async def tools(database: Database) -> ProtocolTools:
    return await harness.tools_for(database, support.SAO_PAULO_PERSON)


def proposal(result: ToolResult[ProtocolProposalDto | ProtocolRefusalDto]) -> ProtocolProposalDto:
    assert isinstance(result.data, ProtocolProposalDto)
    return result.data


def refusal(result: ToolResult[ProtocolProposalDto | ProtocolRefusalDto]) -> ProtocolRefusalDto:
    assert result.status is ToolStatus.REFUSED
    assert isinstance(result.data, ProtocolRefusalDto)
    return result.data


async def test_pr05_free_service_becomes_a_proposal_to_confirm_without_writing(
    tools: ProtocolTools,
) -> None:
    oracle = SqlOracle()
    before = await support.table_counts(oracle)

    result = await tools.propose_protocol(ProtocolAction.DECLARACAO_DE_MATRICULA, SAO_PAULO)

    assert result.status is ToolStatus.OK
    found = proposal(result)
    assert (found.service.code, found.service.sla_hours, found.service.fee_reais) == (
        "DOC-001",
        48,
        Decimal(0),
    )
    assert (found.enrollment, found.requires_confirmation) == (SAO_PAULO, True)
    assert await support.table_counts(oracle) == before


async def test_pr05_the_chosen_one_of_two_enrollments_is_proposed(database: Database) -> None:
    tools = await harness.tools_for(database, support.TWO_ENROLLMENTS_PERSON)
    action = ProtocolAction.SEGUNDA_VIA_DE_BOLETO

    first = await tools.propose_protocol(action, "UniAraucaria:090697")
    second = await tools.propose_protocol(action, "UniAraucaria_EAD:011541")

    assert proposal(first).enrollment == "UniAraucaria:090697"
    assert proposal(second).enrollment == "UniAraucaria_EAD:011541"


async def test_unknown_enrollment_is_not_found_with_the_students_enrollments(
    tools: ProtocolTools,
) -> None:

    result = await tools.propose_protocol(
        ProtocolAction.DECLARACAO_DE_MATRICULA, "UniSaoPaulo:000000"
    )

    assert result.status is ToolStatus.NOT_FOUND
    assert support.candidate_codes(result) == {SAO_PAULO}


async def test_pr07_new_payment_slip_is_proposed(database: Database) -> None:
    tools = await harness.tools_for(database, support.BOLETO_PERSON)

    result = await tools.propose_protocol(
        ProtocolAction.SEGUNDA_VIA_DE_BOLETO, "UniAraucaria_EAD:013161"
    )

    found = proposal(result)
    assert (found.service.code, found.service.sla_hours) == ("FIN-030", 48)


async def test_pr08_a_new_lock_for_a_locked_enrollment_is_refused(database: Database) -> None:
    tools = await harness.tools_for(database, support.LOCKED_PERSON)

    lock = await tools.propose_protocol(ProtocolAction.TRANCAR_CURSO_INTEIRO, LOCKED)
    reactivation = await tools.propose_protocol(ProtocolAction.REATIVAR_MATRICULA, LOCKED)

    refused = refusal(lock)
    assert (refused.reason, refused.service.code) == (RefusalReason.ENROLLMENT_STATUS, "ACA-010")
    assert (lock.client_only, proposal(reactivation).service.code) == (None, "ACA-011")


async def test_a_lock_for_an_active_enrollment_is_a_proposal_for_confirmation(
    tools: ProtocolTools,
) -> None:
    result = await tools.propose_protocol(ProtocolAction.TRANCAR_CURSO_INTEIRO, SAO_PAULO)

    found = proposal(result)
    assert (found.service.code, found.service.sla_hours, found.requires_confirmation) == (
        "ACA-010",
        72,
        True,
    )
    assert (found.course_name_pt, found.limit) == (
        "Ciências Contábeis",
        "Não tranca uma disciplina.",
    )


async def test_equal_request_in_progress_is_refused_with_the_existing_protocol(
    database: Database,
) -> None:
    tools = await harness.tools_for(database, support.DUPLICATE_PERSON)

    enrollment = "UniSaoPaulo_EAD:014214"
    duplicate = await tools.propose_protocol(ProtocolAction.DECLARACAO_DE_MATRICULA, enrollment)
    other = await tools.propose_protocol(ProtocolAction.SEGUNDA_VIA_DE_BOLETO, enrollment)

    refused = refusal(duplicate)
    assert (refused.reason, refused.existing_protocol) == (
        RefusalReason.DUPLICATE_IN_PROGRESS,
        "20260024855",
    )
    assert other.status is ToolStatus.OK


async def test_resolved_request_does_not_block_a_new_one(database: Database) -> None:
    tools = await harness.tools_for(database, support.ARAUCARIA_ONLINE_PERSON)

    result = await tools.propose_protocol(
        ProtocolAction.DECLARACAO_DE_MATRICULA, "UniAraucaria_EAD:012637"
    )

    assert result.status is ToolStatus.OK


async def test_re08_the_proposal_carries_no_text_written_by_the_model(
    tools: ProtocolTools,
) -> None:
    oracle = SqlOracle()
    before = await support.table_counts(oracle)

    result = await tools.propose_protocol(ProtocolAction.PEDIR_DESCONTO_OU_BOLSA, SAO_PAULO)

    found = proposal(result)
    assert (found.service.code, found.requires_confirmation) == ("FIN-032", True)
    assert "message" not in found.model_dump()
    assert await support.table_counts(oracle) == before
