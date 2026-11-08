from dataclasses import replace

import pytest

from api.application.protocol.dto.proposal import Proposal, ProtocolProposalDto, ProtocolRefusalDto
from api.application.protocol.proposer import ProtocolProposer
from api.application.shared.tool_result import ToolResult, ToolStatus
from api.domain.protocol.action import ProtocolAction
from api.domain.protocol.catalog import Service
from api.domain.protocol.proposal import RefusalReason, SignedProposal
from api.domain.shared.money import Money
from tests.unit.protocol import proposal_fakes as fakes

LOCK = ProtocolAction.TRANCAR_CURSO_INTEIRO
REVIEW = ProtocolAction.REVISAR_NOTA
SUBJECT = "Direito Empresarial"


def proposer(
    protocols: fakes.FakeProtocols | None = None, signer: fakes.RecordingSigner | None = None
) -> ProtocolProposer:
    return ProtocolProposer(
        protocols or fakes.FakeProtocols(),
        fakes.FakeAcademic(),
        signer or fakes.RecordingSigner(),
        fakes.SESSION,
    )


def proposal(result: ToolResult[Proposal]) -> ProtocolProposalDto:
    assert result.status is ToolStatus.OK
    assert isinstance(result.data, ProtocolProposalDto)
    return result.data


def refusal(result: ToolResult[Proposal]) -> ProtocolRefusalDto:
    assert result.status is ToolStatus.REFUSED
    assert isinstance(result.data, ProtocolRefusalDto)
    return result.data


async def test_a_subject_in_an_action_for_the_whole_course_is_refused_with_an_explanation() -> None:
    signer = fakes.RecordingSigner()

    result = await proposer(signer=signer).propose(LOCK, fakes.ACTIVE.reference, SUBJECT)

    refused = refusal(result)
    assert (refused.reason, refused.service.code) == (
        RefusalReason.SUBJECT_NOT_SUPPORTED,
        "ACA-010",
    )
    assert (result.client_only, signer.signed) == (None, [])
    explanation = result.explanation or ""
    assert {"não existe" in explanation, "curso inteiro" in explanation} == {True}
    assert SUBJECT not in explanation


async def test_a_blank_subject_counts_as_no_subject() -> None:
    result = await proposer().propose(LOCK, fakes.ACTIVE.reference, "  ")

    assert proposal(result).subject is None


async def test_an_action_that_takes_a_subject_keeps_it_in_the_proposal_only() -> None:
    signer = fakes.RecordingSigner()

    result = await proposer(signer=signer).propose(REVIEW, fakes.ACTIVE.reference, SUBJECT)

    assert proposal(result).subject == SUBJECT
    assert proposal(result).requires_student_message is True
    assert signer.signed == [SignedProposal(fakes.PERSON, fakes.ACTIVE.reference, "ACA-020")]


async def test_an_enrollment_outside_the_accepted_statuses_is_refused() -> None:
    signer = fakes.RecordingSigner()

    result = await proposer(signer=signer).propose(LOCK, fakes.LOCKED.reference, None)

    assert refusal(result).reason is RefusalReason.ENROLLMENT_STATUS
    assert (result.client_only, signer.signed) == (None, [])
    explanation = result.explanation or ""
    assert {"locked" in explanation, "active" in explanation} == {True}


async def test_the_proposal_carries_the_catalog_texts_and_the_portuguese_course() -> None:
    result = await proposer().propose(LOCK, fakes.ACTIVE.reference, None)

    found = proposal(result)
    assert (found.service.code, found.enrollment) == ("ACA-010", fakes.ACTIVE.reference)
    assert (found.title, found.limit) == ("Trancamento do curso", "Não tranca uma disciplina.")
    assert found.effect.startswith("Tranca a matrícula no curso inteiro")
    assert (found.course_name, found.course_name_pt) == ("Accounting", "Ciências Contábeis")
    assert (found.requires_student_message, found.requires_confirmation) == (False, True)


async def test_the_client_gets_the_token_and_the_confirmation_block() -> None:
    result = await proposer().propose(LOCK, fakes.ACTIVE.reference, None)

    assert result.client_only == {
        "token": fakes.SIGNED,
        "confirmation": {
            "question": "Tem certeza de que deseja trancar o curso Ciências Contábeis?",
            "effect": proposal(result).effect,
            "limit": "Não tranca uma disciplina.",
            "word": "TRANCAR",
        },
    }
    dumped = result.model_dump_json()
    assert "TRANCAR" not in dumped
    assert "Tem certeza" not in dumped


async def test_an_action_without_a_word_sends_the_word_as_null() -> None:
    result = await proposer().propose(
        ProtocolAction.INFORMACOES_GERAIS, fakes.ACTIVE.reference, None
    )

    assert result.client_only is not None
    confirmation = result.client_only["confirmation"]
    assert not isinstance(confirmation, str)
    assert confirmation["word"] is None
    assert confirmation["question"]


async def test_an_unknown_enrollment_is_not_found_with_the_students_enrollments() -> None:
    result = await proposer().propose(LOCK, "UniSaoPaulo:000000", None)

    assert result.status is ToolStatus.NOT_FOUND
    assert {item.code for item in result.candidates} == {
        fakes.ACTIVE.reference,
        fakes.LOCKED.reference,
    }


async def test_a_service_missing_from_the_source_fails_closed() -> None:
    protocols = fakes.FakeProtocols(services=(fakes.GRADE_REVIEW,))

    result = await proposer(protocols).propose(LOCK, fakes.ACTIVE.reference, None)

    assert (result.status, result.client_only) == (ToolStatus.NOT_FOUND, None)


@pytest.mark.parametrize(
    ("service", "reason"),
    [
        pytest.param(replace(fakes.LOCK, fee=Money(4500)), RefusalReason.SERVICE_HAS_FEE, id="fee"),
        pytest.param(replace(fakes.LOCK, active=False), RefusalReason.SERVICE_INACTIVE, id="off"),
    ],
)
async def test_a_service_the_agent_cannot_open_is_refused(
    service: Service, reason: RefusalReason
) -> None:
    protocols = fakes.FakeProtocols(services=(service,))

    result = await proposer(protocols).propose(LOCK, fakes.ACTIVE.reference, None)

    assert refusal(result).reason is reason
