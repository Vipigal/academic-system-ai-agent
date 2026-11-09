from datetime import date
from decimal import Decimal

import pytest

from api.application.academic.dto.catalog import CourseOfferDto
from api.application.academic.dto.enrollment import EnrollmentDto
from api.domain.academic.course import CourseNames
from api.domain.academic.enrollment import CourseOffer, Enrollment, EnrollmentStatus, Shift
from api.domain.shared.brand import Brand, Modality

COURSE_ACRONYMS = {"ADM", "ADS", "CON", "PED", "DIR", "ENF", "ENC", "PSI"}
ENROLLMENT = Enrollment(
    reference="UniSaoPaulo:181722",
    brand=Brand.SAO_PAULO,
    course_code="CON",
    course_name="ACCOUNTING",
    curriculum_id="CON-2024",
    curriculum_hours=3000,
    unit_name="Unit",
    modality=Modality.IN_PERSON,
    shift=Shift.EVENING,
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
OFFER = CourseOffer(
    id="1",
    course_code="ADS",
    course_name="SYSTEMS ANALYSIS & DEVELOPMENT",
    unit_id="10",
    unit_name="Unit",
    city="São Paulo",
    state="SP",
    shift=Shift.ONLINE,
)


def test_the_eight_courses_have_a_portuguese_name() -> None:
    assert {code for code in COURSE_ACRONYMS if CourseNames.portuguese(code)} == COURSE_ACRONYMS


@pytest.mark.parametrize(
    ("code", "name"),
    [("CON", "Ciências Contábeis"), ("ADS", "Análise e Desenvolvimento de Sistemas")],
)
def test_the_portuguese_name_is_the_course_name(code: str, name: str) -> None:
    assert CourseNames.portuguese(code) == name


def test_an_unknown_course_has_no_portuguese_name() -> None:
    assert CourseNames.portuguese("XYZ") is None


def test_the_enrollment_shows_the_portuguese_course_name() -> None:
    dto = EnrollmentDto.from_entity(ENROLLMENT, "2026/2")

    assert (dto.course_name, dto.course_name_pt) == ("ACCOUNTING", "Ciências Contábeis")


def test_the_course_offer_shows_the_portuguese_course_name() -> None:
    dto = CourseOfferDto.from_entity(OFFER)

    assert dto.course_name_pt == "Análise e Desenvolvimento de Sistemas"
