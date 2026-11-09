import logging
from uuid import uuid4

import pytest

from api.domain.conversation.errors import ConversationNotFoundError
from api.domain.conversation.message import MessageRole
from api.domain.protocol.errors import ProposalNotFoundError, ServiceNotOpenableError
from api.domain.protocol.opening import StudentAnswer
from api.domain.protocol.proposal import RefusalReason, SignedProposal
from tests.unit.protocol import confirmation_fakes as bench
from tests.unit.protocol import proposal_fakes as fakes
from tests.unit.protocol.catalog_actions import DECLARATION, INFORMATION

CONVERSATION = str(bench.CONVERSATION)
TYPED = "Quero saber quando sai a nota da AV2 de Gestão Estratégica II."
WRITTEN = StudentAnswer(message=TYPED, word="")


async def test_a_free_text_service_records_what_the_student_typed() -> None:
    confirmed = bench.ConfirmationBench()

    result = await confirmed.confirmation().confirm(
        confirmed.token_for(INFORMATION.code), CONVERSATION, WRITTEN
    )

    assert result.protocol_number == bench.NUMBER
    assert [opening.message for opening in confirmed.writer.saved] == [TYPED]


async def test_a_simple_service_records_the_fixed_text_and_ignores_the_message() -> None:
    confirmed = bench.ConfirmationBench()

    await confirmed.confirmation().confirm(
        confirmed.token_for(DECLARATION.code), CONVERSATION, WRITTEN
    )

    assert [opening.message for opening in confirmed.writer.saved] == [DECLARATION.request_text]


async def test_the_event_tells_number_title_course_and_deadline_without_the_typed_text() -> None:
    confirmed = bench.ConfirmationBench()

    await confirmed.confirmation().confirm(
        confirmed.token_for(INFORMATION.code), CONVERSATION, WRITTEN
    )

    [event] = confirmed.conversations.appended
    assert event.role is MessageRole.SYSTEM_EVENT
    for told in (bench.NUMBER, INFORMATION.title, "Ciências Contábeis", "03/11/2026"):
        assert told in event.content
    assert TYPED not in event.content


@pytest.mark.parametrize("conversation", [str(uuid4()), "nao-e-uuid"], ids=["unknown", "malformed"])
async def test_a_conversation_out_of_reach_is_not_found_and_nothing_is_written(
    conversation: str,
) -> None:
    confirmed = bench.ConfirmationBench()

    with pytest.raises(ConversationNotFoundError):
        await confirmed.confirmation().confirm(
            confirmed.token_for(INFORMATION.code), conversation, WRITTEN
        )

    assert (confirmed.writer.saved, confirmed.conversations.appended) == ([], [])


async def test_a_token_of_another_person_is_not_found() -> None:
    confirmed = bench.ConfirmationBench()
    alien = confirmed.signer.sign(SignedProposal("9999999", fakes.ACTIVE.reference, "GEN-090"))

    with pytest.raises(ProposalNotFoundError):
        await confirmed.confirmation().confirm(alien, CONVERSATION, WRITTEN)

    assert confirmed.writer.saved == []


@pytest.mark.parametrize(
    ("service", "enrollment", "answer", "expected"),
    [
        pytest.param(
            "GEN-090",
            fakes.ACTIVE.reference,
            StudentAnswer(" ", ""),
            RefusalReason.EMPTY_MESSAGE,
            id="blank",
        ),
        pytest.param(
            "GEN-090",
            fakes.ACTIVE.reference,
            StudentAnswer("x" * 4001, ""),
            RefusalReason.MESSAGE_TOO_LONG,
            id="too-long",
        ),
        pytest.param(
            "ACA-010",
            fakes.ACTIVE.reference,
            StudentAnswer("", ""),
            RefusalReason.CONFIRMATION_WORD,
            id="no-word",
        ),
        pytest.param(
            "ACA-010",
            fakes.ACTIVE.reference,
            StudentAnswer("", "CANCELAR"),
            RefusalReason.CONFIRMATION_WORD,
            id="wrong-word",
        ),
        pytest.param(
            "ACA-011",
            fakes.ACTIVE.reference,
            StudentAnswer("", ""),
            RefusalReason.ENROLLMENT_STATUS,
            id="enrollment-status",
        ),
        pytest.param(
            bench.PAID_SLIP.code,
            fakes.ACTIVE.reference,
            StudentAnswer("", ""),
            RefusalReason.SERVICE_HAS_FEE,
            id="fee",
        ),
    ],
)
async def test_a_refused_answer_writes_neither_protocol_nor_event(
    service: str, enrollment: str, answer: StudentAnswer, expected: RefusalReason
) -> None:
    confirmed = bench.ConfirmationBench()

    with pytest.raises(ServiceNotOpenableError) as refused:
        await confirmed.confirmation().confirm(
            confirmed.token_for(service, enrollment), CONVERSATION, answer
        )

    assert refused.value.reason is expected
    assert (confirmed.writer.saved, confirmed.conversations.appended) == ([], [])


async def test_the_word_is_accepted_in_any_case_and_with_outer_spaces() -> None:
    confirmed = bench.ConfirmationBench()

    await confirmed.confirmation().confirm(
        confirmed.token_for("ACA-010"), CONVERSATION, StudentAnswer("", " trancar ")
    )

    assert [opening.service_code for opening in confirmed.writer.saved] == ["ACA-010"]


async def test_a_position_collision_is_retried_once() -> None:
    confirmed = bench.ConfirmationBench(conversations=bench.FakeConversations(conflicts=1))

    await confirmed.confirmation().confirm(
        confirmed.token_for(INFORMATION.code), CONVERSATION, WRITTEN
    )

    assert len(confirmed.conversations.appended) == 1


async def test_a_second_collision_keeps_the_protocol_and_logs_an_error(
    caplog: pytest.LogCaptureFixture,
) -> None:
    confirmed = bench.ConfirmationBench(conversations=bench.FakeConversations(conflicts=2))

    with caplog.at_level(logging.INFO, logger="api.application.protocol"):
        result = await confirmed.confirmation().confirm(
            confirmed.token_for(INFORMATION.code), CONVERSATION, WRITTEN
        )

    assert result.protocol_number == bench.NUMBER
    assert confirmed.conversations.appended == []
    assert logging.ERROR in {record.levelno for record in caplog.records}
    assert TYPED not in caplog.text


async def test_a_failed_event_write_keeps_the_protocol_and_logs_an_error(
    caplog: pytest.LogCaptureFixture,
) -> None:
    confirmed = bench.ConfirmationBench(conversations=bench.FakeConversations(broken=True))

    with caplog.at_level(logging.INFO, logger="api.application.protocol"):
        result = await confirmed.confirmation().confirm(
            confirmed.token_for(INFORMATION.code), CONVERSATION, WRITTEN
        )

    assert result.protocol_number == bench.NUMBER
    assert len(confirmed.writer.saved) == 1
    assert confirmed.conversations.appended == []
    assert logging.ERROR in {record.levelno for record in caplog.records}
    assert TYPED not in caplog.text


async def test_a_code_without_an_action_in_the_catalog_is_not_found() -> None:
    confirmed = bench.ConfirmationBench()

    with pytest.raises(ProposalNotFoundError):
        await confirmed.confirmation().confirm(
            confirmed.token_for(bench.TRANSCRIPT.code), CONVERSATION, WRITTEN
        )

    assert (confirmed.writer.saved, confirmed.conversations.appended) == ([], [])
