from dataclasses import replace

import pytest

from api.domain.academic.enrollment import EnrollmentStatus
from api.domain.protocol.action import ProtocolAction
from api.domain.protocol.action_catalog import ServiceActions
from api.domain.protocol.proposal import ProposalRules, RefusalReason
from tests.unit.protocol import proposal_fakes as fakes

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
