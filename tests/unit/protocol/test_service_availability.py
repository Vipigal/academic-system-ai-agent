from dataclasses import replace

import pytest

from api.application.protocol.dto.catalog import ServiceOfferDto
from api.domain.academic.enrollment import Enrollment, EnrollmentStatus
from api.domain.protocol.availability import ServiceAvailability, Unavailability
from api.domain.protocol.catalog import Service
from api.domain.shared.money import Money
from tests.unit.protocol.proposal_fakes import ACTIVE, GRADE_REVIEW, INFORMATION, LOCK, LOCKED

CANCELLED = replace(ACTIVE, status=EnrollmentStatus.CANCELLED)
REACTIVATION = replace(LOCK, code="ACA-011", name="Enrollment Reactivation")
SECOND_CALL = replace(LOCK, code="ACA-021", name="Second-Call Exam", fee=Money(4500))
UNKNOWN = replace(LOCK, code="XYZ-999", name="Unknown Service")


@pytest.mark.parametrize(
    ("service", "enrollments", "expected"),
    [
        (LOCK, (ACTIVE,), None),
        (LOCK, (LOCKED,), Unavailability.ENROLLMENT_STATUS),
        (LOCK, (CANCELLED,), Unavailability.ENROLLMENT_STATUS),
        (LOCK, (CANCELLED, ACTIVE), None),
        (REACTIVATION, (LOCKED,), None),
        (GRADE_REVIEW, (CANCELLED,), Unavailability.ENROLLMENT_STATUS),
        (INFORMATION, (CANCELLED,), None),
        (SECOND_CALL, (ACTIVE,), Unavailability.SERVICE_HAS_FEE),
        (replace(LOCK, active=False), (ACTIVE,), Unavailability.SERVICE_INACTIVE),
        (UNKNOWN, (ACTIVE,), Unavailability.HANDLED_BY_SECRETARY),
    ],
    ids=lambda value: value.code if isinstance(value, Service) else None,
)
def test_a_service_is_available_only_for_a_status_it_accepts(
    service: Service, enrollments: tuple[Enrollment, ...], expected: Unavailability | None
) -> None:
    assert ServiceAvailability.of(service, enrollments) is expected


def test_without_enrollment_no_service_that_needs_one_is_available() -> None:
    assert ServiceAvailability.of(INFORMATION, ()) is Unavailability.ENROLLMENT_STATUS


def test_the_offer_explains_which_status_the_service_accepts() -> None:
    offer = ServiceOfferDto.of(LOCK, (CANCELLED,))

    assert (offer.available, offer.unavailable_reason) == (
        False,
        "Aceita só matrícula com situação active, e nenhuma matrícula do aluno está assim.",
    )


def test_an_available_offer_has_no_reason() -> None:
    offer = ServiceOfferDto.of(INFORMATION, (CANCELLED,))

    assert (offer.available, offer.unavailable_reason) == (True, None)
