from dataclasses import replace
from datetime import date, datetime, timedelta
from decimal import Decimal

import pytest

from api.domain.academic import Enrollment, EnrollmentStatus, Shift
from api.domain.brand import Brand, Modality
from api.domain.money import Money
from api.domain.protocol import Protocol, Requester
from api.domain.protocol_catalog import Service, ServiceArea
from api.domain.protocol_proposal import ProposalRules, ProtocolNumber, RefusalReason
from api.domain.protocol_status import DeadlineSituation, ProtocolStage, ProtocolStatus
from api.persistence.brasilia import BRASILIA

DUE = datetime(2026, 11, 1, 14, 50, tzinfo=BRASILIA)
SERVICE = Service(
    code="DOC-001",
    name="Enrollment Certificate",
    area=ServiceArea.DOCUMENTS,
    sla_hours=48,
    fee=Money(0),
    active=True,
)
PROTOCOL = Protocol(
    number="20260000001",
    service=SERVICE,
    status=ProtocolStatus.IN_ANALYSIS,
    resolution=None,
    requester=Requester.SELF,
    brand=Brand.SAO_PAULO,
    modality=Modality.IN_PERSON,
    enrollment_reference="UniSaoPaulo:181722",
    course_label="Accounting",
    opened_at=DUE - timedelta(hours=48),
    first_response_at=None,
    due_at=DUE,
    closed_at=None,
    documents=(),
    history=(),
    messages=(),
)


@pytest.mark.parametrize(
    ("reference", "situation"),
    [
        (date(2026, 10, 31), DeadlineSituation.WITHIN_DEADLINE),
        (date(2026, 11, 1), DeadlineSituation.WITHIN_DEADLINE),
        (date(2026, 11, 2), DeadlineSituation.OVERDUE),
    ],
)
def test_open_protocol_is_overdue_only_after_the_due_day(
    reference: date, situation: DeadlineSituation
) -> None:
    assert PROTOCOL.deadline(reference) is situation


def test_closed_protocol_compares_the_closing_with_the_due_moment() -> None:
    on_time = replace(PROTOCOL, closed_at=DUE - timedelta(hours=1))
    late = replace(PROTOCOL, closed_at=DUE + timedelta(hours=1))

    assert on_time.deadline(date(2030, 1, 1)) is DeadlineSituation.MET
    assert late.deadline(date(2030, 1, 1)) is DeadlineSituation.MISSED


@pytest.mark.parametrize(
    ("status", "stage"),
    [
        (ProtocolStatus.OPEN, ProtocolStage.IN_PROGRESS),
        (ProtocolStatus.PENDING_REQUESTER, ProtocolStage.IN_PROGRESS),
        (ProtocolStatus.RESOLVED, ProtocolStage.RESOLVED),
        (ProtocolStatus.CANCELLED, ProtocolStage.CANCELLED),
    ],
)
def test_status_maps_to_stage(status: ProtocolStatus, stage: ProtocolStage) -> None:
    assert replace(PROTOCOL, status=status).stage is stage


@pytest.mark.parametrize("text", ["PRT-2026/0024630", "20260024630", " 2026 0024630 "])
def test_number_keeps_only_digits(text: str) -> None:
    assert ProtocolNumber.digits(text) == "20260024630"


def test_refusal_reasons() -> None:
    with_fee = replace(SERVICE, fee=Money(4500))

    assert ProposalRules.refusal(SERVICE, "texto") is None
    assert ProposalRules.refusal(with_fee, "texto") is RefusalReason.SERVICE_HAS_FEE
    assert ProposalRules.refusal(replace(SERVICE, active=False), "x") is (
        RefusalReason.SERVICE_INACTIVE
    )
    assert ProposalRules.refusal(SERVICE, " ") is RefusalReason.EMPTY_MESSAGE


def enrollment(reference: str, brand: Brand, modality: Modality) -> Enrollment:
    return Enrollment(
        reference=reference,
        brand=brand,
        course_code="CCO",
        course_name="Accounting",
        curriculum_id="CCO-2024",
        curriculum_hours=3000,
        unit_name="Unit",
        modality=modality,
        shift=Shift.MORNING,
        status=EnrollmentStatus.ACTIVE,
        status_date=date(2024, 2, 1),
        entry_term="2024/1",
        semester=3,
        completion_pct=Decimal(40),
        gpa=None,
        origin_reference=None,
        registrations={},
        history=(),
    )


OWN = enrollment("UniSaoPaulo:181722", Brand.SAO_PAULO, Modality.IN_PERSON)
OTHER = enrollment("UniSaoPaulo:180882", Brand.SAO_PAULO, Modality.IN_PERSON)
ONLINE = enrollment("UniSaoPaulo_EAD:012831", Brand.SAO_PAULO, Modality.ONLINE)


def test_duplicate_matches_the_same_service_and_enrollment_in_progress() -> None:
    assert ProposalRules.duplicate_of([PROTOCOL], SERVICE, OWN) is PROTOCOL
    assert ProposalRules.duplicate_of([PROTOCOL], SERVICE, OTHER) is None


def test_duplicate_ignores_other_services_and_closed_protocols() -> None:
    other_service = replace(PROTOCOL, service=replace(SERVICE, code="FIN-030"))
    resolved = replace(PROTOCOL, status=ProtocolStatus.RESOLVED)

    assert ProposalRules.duplicate_of([other_service, resolved], SERVICE, OWN) is None


def test_duplicate_without_enrollment_reference_matches_by_brand_and_modality() -> None:
    without_id = replace(PROTOCOL, enrollment_reference=None)

    assert ProposalRules.duplicate_of([without_id], SERVICE, OWN) is without_id
    assert ProposalRules.duplicate_of([without_id], SERVICE, ONLINE) is None
