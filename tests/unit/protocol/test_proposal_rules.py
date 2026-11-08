from dataclasses import replace
from datetime import date

import pytest

from api.domain.academic.enrollment import Enrollment, EnrollmentStatus
from api.domain.protocol.action import ProtocolAction, ServiceAction
from api.domain.protocol.action_catalog import ServiceActions
from api.domain.protocol.errors import ServiceNotOpenableError
from api.domain.protocol.opening import OpeningRequest, ProtocolOpening, StudentAnswer
from api.domain.protocol.proposal import ProposalRules, RefusalReason
from tests.unit.protocol import proposal_fakes as fakes
from tests.unit.protocol.catalog_actions import DECLARATION, INFORMATION, LOCK

STATUS_REFUSED = RefusalReason.ENROLLMENT_STATUS


def test_a_subject_is_refused_only_by_the_actions_that_do_not_take_one() -> None:
    lock = ServiceActions.of_action(ProtocolAction.TRANCAR_CURSO_INTEIRO)
    review = ServiceActions.of_action(ProtocolAction.REVISAR_NOTA)

    assert ProposalRules.action_refusal(lock, "Direito Empresarial") is (
        RefusalReason.SUBJECT_NOT_SUPPORTED
    )
    assert ProposalRules.action_refusal(lock, None) is None
    assert ProposalRules.action_refusal(review, "Direito Empresarial") is None


@pytest.mark.parametrize(
    ("action", "status", "expected"),
    [
        (ProtocolAction.TRANCAR_CURSO_INTEIRO, EnrollmentStatus.ACTIVE, None),
        (ProtocolAction.TRANCAR_CURSO_INTEIRO, EnrollmentStatus.LOCKED, STATUS_REFUSED),
        (ProtocolAction.REATIVAR_MATRICULA, EnrollmentStatus.ACTIVE, STATUS_REFUSED),
        (ProtocolAction.REATIVAR_MATRICULA, EnrollmentStatus.LOCKED, None),
        (ProtocolAction.DECLARACAO_DE_MATRICULA, EnrollmentStatus.GRADUATED, None),
    ],
)
def test_the_enrollment_status_must_be_one_the_action_accepts(
    action: ProtocolAction, status: EnrollmentStatus, expected: RefusalReason | None
) -> None:
    chosen = replace(fakes.ACTIVE, status=status)

    reason = ProposalRules.enrollment_refusal(ServiceActions.of_action(action), chosen)

    assert reason is expected


LONGEST = "x" * 4000


@pytest.mark.parametrize(
    ("action", "message", "expected"),
    [
        pytest.param(INFORMATION, "Quando sai a nota?", None, id="free-text-written"),
        pytest.param(INFORMATION, "  ", RefusalReason.EMPTY_MESSAGE, id="free-text-blank"),
        pytest.param(INFORMATION, LONGEST, None, id="free-text-at-the-limit"),
        pytest.param(
            INFORMATION, f"{LONGEST}x", RefusalReason.MESSAGE_TOO_LONG, id="free-text-too-long"
        ),
        pytest.param(DECLARATION, "", None, id="fixed-text-without-message"),
        pytest.param(
            DECLARATION, f"{LONGEST}x", RefusalReason.MESSAGE_TOO_LONG, id="fixed-text-too-long"
        ),
    ],
)
def test_the_message_is_required_only_by_free_text_and_never_above_the_limit(
    action: ServiceAction, message: str, expected: RefusalReason | None
) -> None:
    assert ProposalRules.message_refusal(action, message) is expected


@pytest.mark.parametrize(
    ("action", "word", "expected"),
    [
        pytest.param(LOCK, "TRANCAR", None, id="exact"),
        pytest.param(LOCK, "  trancar ", None, id="any-case-and-outer-spaces"),
        pytest.param(LOCK, "", RefusalReason.CONFIRMATION_WORD, id="missing"),
        pytest.param(LOCK, "CANCELAR", RefusalReason.CONFIRMATION_WORD, id="wrong"),
        pytest.param(LOCK, "TRAN CAR", RefusalReason.CONFIRMATION_WORD, id="inner-space"),
        pytest.param(DECLARATION, "", None, id="action-without-word"),
        pytest.param(DECLARATION, "qualquer", None, id="word-ignored-without-one"),
    ],
)
def test_the_confirmation_word_is_required_only_where_the_action_has_one(
    action: ServiceAction, word: str, expected: RefusalReason | None
) -> None:
    assert ProposalRules.word_refusal(action, word) is expected


@pytest.mark.parametrize(
    ("action", "answer", "enrollment", "expected"),
    [
        pytest.param(
            INFORMATION,
            StudentAnswer("   ", ""),
            fakes.ACTIVE,
            RefusalReason.EMPTY_MESSAGE,
            id="blank",
        ),
        pytest.param(
            LOCK,
            StudentAnswer("", "cancelar"),
            fakes.ACTIVE,
            RefusalReason.CONFIRMATION_WORD,
            id="wrong-word",
        ),
        pytest.param(
            LOCK,
            StudentAnswer("", "trancar"),
            fakes.LOCKED,
            RefusalReason.ENROLLMENT_STATUS,
            id="enrollment-status",
        ),
    ],
)
def test_the_opening_checks_what_the_student_sent_against_the_action(
    action: ServiceAction, answer: StudentAnswer, enrollment: Enrollment, expected: RefusalReason
) -> None:
    request = OpeningRequest("Maria Souza", action, answer, date(2026, 10, 31))

    with pytest.raises(ServiceNotOpenableError) as refused:
        ProtocolOpening.open(fakes.LOCK, enrollment, (), request)

    assert refused.value.reason is expected
