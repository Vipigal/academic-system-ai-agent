from dataclasses import replace
from datetime import UTC, date, datetime
from decimal import Decimal

import pytest

from api.domain.academic.enrollment import Enrollment, EnrollmentStatus, Shift
from api.domain.protocol.catalog import Service, ServiceArea
from api.domain.protocol.errors import DuplicateProtocolError, ServiceNotOpenableError
from api.domain.protocol.opening import OpeningRequest, ProtocolOpening
from api.domain.protocol.request import Protocol, Requester
from api.domain.protocol.status import ProtocolStatus
from api.domain.shared.brand import Brand, Modality
from api.domain.shared.money import Money

OPENED_AT = datetime(2026, 10, 31, 3, 0, tzinfo=UTC)
DUE_AT = datetime(2026, 11, 2, 3, 0, tzinfo=UTC)
SERVICE = Service(
    code="DOC-001",
    name="Enrollment Certificate",
    area=ServiceArea.DOCUMENTS,
    sla_hours=48,
    fee=Money(0),
    active=True,
)
ENROLLMENT = Enrollment(
    reference="UniSaoPaulo:181722",
    brand=Brand.SAO_PAULO,
    course_code="ADM",
    course_name="Administration",
    curriculum_id="1",
    curriculum_hours=3000,
    unit_name="CAMPUS PAULISTA",
    modality=Modality.IN_PERSON,
    shift=Shift.MORNING,
    status=EnrollmentStatus.ACTIVE,
    status_date=date(2026, 2, 1),
    entry_term="2026-1",
    semester=1,
    completion_pct=Decimal(10),
    gpa=None,
    origin_reference=None,
    registrations={},
    history=(),
)
EXISTING = Protocol(
    number="20260000001",
    service=SERVICE,
    status=ProtocolStatus.OPEN,
    resolution=None,
    requester=Requester.SELF,
    brand=Brand.SAO_PAULO,
    modality=Modality.IN_PERSON,
    enrollment_reference=ENROLLMENT.reference,
    course_label="Administration",
    opened_at=OPENED_AT,
    first_response_at=None,
    due_at=DUE_AT,
    closed_at=None,
    documents=(),
    history=(),
    messages=(),
)
REQUEST = OpeningRequest(requester_name="Maria Souza", message="Preciso", today=date(2026, 10, 31))


def test_a_protocol_opens_at_the_start_of_the_day_in_brasilia_with_the_service_sla() -> None:
    opening = ProtocolOpening.open(SERVICE, ENROLLMENT, (), REQUEST)
    assert opening.status is ProtocolStatus.OPEN
    assert opening.opened_at == OPENED_AT
    assert opening.due_at == DUE_AT


def test_the_opening_carries_the_first_change_and_the_message_of_the_requester() -> None:
    opening = ProtocolOpening.open(SERVICE, ENROLLMENT, (), REQUEST)
    assert (opening.first_change.status, opening.first_change.changed_at) == (
        ProtocolStatus.OPEN,
        OPENED_AT,
    )
    assert (opening.message, opening.requester_name) == (REQUEST.message, REQUEST.requester_name)


def test_the_opening_comes_from_the_enrollment() -> None:
    opening = ProtocolOpening.open(SERVICE, ENROLLMENT, (), REQUEST)
    assert (opening.enrollment_reference, opening.unit_name, opening.course_name) == (
        ENROLLMENT.reference,
        ENROLLMENT.unit_name,
        ENROLLMENT.course_name,
    )


@pytest.mark.parametrize(
    "service",
    [
        pytest.param(replace(SERVICE, fee=Money(2000)), id="with-a-fee"),
        pytest.param(replace(SERVICE, active=False), id="inactive"),
    ],
)
def test_a_service_the_agent_cannot_open_is_refused(service: Service) -> None:
    with pytest.raises(ServiceNotOpenableError):
        ProtocolOpening.open(service, ENROLLMENT, (), REQUEST)


def test_a_blank_message_is_refused() -> None:
    with pytest.raises(ServiceNotOpenableError):
        ProtocolOpening.open(SERVICE, ENROLLMENT, (), replace(REQUEST, message="   "))


def test_an_equal_request_in_progress_is_refused() -> None:
    with pytest.raises(DuplicateProtocolError):
        ProtocolOpening.open(SERVICE, ENROLLMENT, (EXISTING,), REQUEST)


def test_personal_data_stays_out_of_the_repr() -> None:
    opening = ProtocolOpening.open(SERVICE, ENROLLMENT, (), REQUEST)
    assert REQUEST.requester_name not in repr(opening)
    assert REQUEST.requester_name not in repr(REQUEST)
