from datetime import date
from decimal import Decimal

from api.domain.academic.enrollment import Shift
from api.domain.academic.record import Delivery, Grades, SubjectRecord, SubjectResult
from api.domain.academic.term_calendar import Term

REFERENCE = date(2026, 10, 31)
OPEN_TERM = Term(
    code="2026/2",
    start_date=date(2026, 8, 1),
    end_date=date(2026, 12, 15),
    av1_start=date(2026, 10, 3),
    av2_start=date(2026, 12, 5),
    is_current=True,
)


def record(
    av1: str | None = None,
    attendance: str | None = None,
    result: SubjectResult = SubjectResult.IN_PROGRESS,
    delivery: Delivery = Delivery.IN_PERSON,
) -> SubjectRecord:
    return SubjectRecord(
        enrollment="UniMontanhas:070793",
        class_id="1",
        term=OPEN_TERM,
        subject_code="DIR0301",
        subject_name="CRIMINAL LAW I",
        section="T01",
        shift=Shift.EVENING,
        delivery=delivery,
        unit_name="CAMPUS",
        is_retake=False,
        grades=Grades(av1=None if av1 is None else Decimal(av1), av2=None, av3=None, final=None),
        attendance_pct=None if attendance is None else Decimal(attendance),
        result=result,
    )


def test_required_av2_applies_the_observed_weights() -> None:
    assert record(av1="4.3").required_av2() == Decimal("7.1")


def test_required_av2_needs_av1_and_a_subject_in_progress() -> None:
    assert record().required_av2() is None
    assert record(av1="4.3", result=SubjectResult.FAILED).required_av2() is None


def test_grade_is_awaited_only_before_its_date_and_when_the_subject_has_grades() -> None:
    assert record().grade_is_awaited(OPEN_TERM.av2_start, REFERENCE)
    assert not record().grade_is_awaited(OPEN_TERM.av1_start, REFERENCE)
    assert not record(result=SubjectResult.EXEMPT).grade_is_awaited(OPEN_TERM.av2_start, REFERENCE)


def test_attendance_rule_is_used_online_and_at_or_below_the_limit() -> None:
    assert record(delivery=Delivery.ONLINE).uses_attendance_rule
    assert record(attendance="75.0").uses_attendance_rule
    assert not record(attendance="75.1").uses_attendance_rule
    assert not record(delivery=Delivery.EXEMPTION).uses_attendance_rule
