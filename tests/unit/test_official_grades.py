from datetime import UTC, date, datetime
from decimal import Decimal

from api.application.lms_scope import OfficialGrades
from api.domain.academic import Enrollment, EnrollmentStatus, Shift
from api.domain.academic_calendar import Term
from api.domain.academic_curriculum import EnrollmentProgress
from api.domain.academic_record import Delivery, Grades, SubjectRecord, SubjectResult
from api.domain.brand import Brand, Modality
from api.domain.lms import ExamKind, OnlineExam

TERM = Term(
    code="2026/2",
    start_date=date(2026, 8, 1),
    end_date=date(2026, 12, 15),
    av1_start=date(2026, 10, 3),
    av2_start=date(2026, 12, 5),
    is_current=True,
)
MOMENT = datetime(2026, 10, 5, 8, 0, tzinfo=UTC)
TODAY = date(2026, 10, 31)


def enrollment(brand: Brand, reference: str) -> Enrollment:
    return Enrollment(
        reference=reference,
        brand=brand,
        course_code="C",
        course_name="Course",
        curriculum_id="1",
        curriculum_hours=100,
        unit_name="Unit",
        modality=Modality.IN_PERSON,
        shift=Shift.EVENING,
        status=EnrollmentStatus.ACTIVE,
        status_date=TODAY,
        entry_term="2026/1",
        semester=1,
        completion_pct=Decimal(0),
        gpa=None,
        origin_reference=None,
        registrations={},
        history=(),
    )


def progress(brand: Brand, reference: str, av1: str) -> EnrollmentProgress:
    record = SubjectRecord(
        enrollment=reference,
        class_id="1",
        term=TERM,
        subject_code="DIR0301",
        subject_name="LAW",
        section="T01",
        shift=Shift.EVENING,
        delivery=Delivery.IN_PERSON,
        unit_name=None,
        is_retake=False,
        grades=Grades(av1=Decimal(av1), av2=None, av3=None, final=None),
        attendance_pct=None,
        result=SubjectResult.IN_PROGRESS,
    )
    return EnrollmentProgress.of(enrollment(brand, reference), (), (record,))


def exam(brand: Brand) -> OnlineExam:
    return OnlineExam(
        quiz_id="1",
        brand=brand,
        subject_code="DIR0301",
        subject_name="LAW",
        term="2026/2",
        delivery=Delivery.IN_PERSON,
        kind=ExamKind.AV1,
        opens_at=MOMENT,
        closes_at=MOMENT,
        time_limit_minutes=60,
        max_attempts=1,
        attempts=(),
    )


def test_two_enrollments_with_the_same_subject_and_term_keep_separate_records() -> None:
    first = progress(Brand.MONTANHAS, "UniMontanhas:070793", "4.0")
    second = progress(Brand.LITORAL, "UniLitoral:010101", "9.0")
    index = OfficialGrades.records_by_class([first, second])
    assert len(index) == 2
    assert index[Brand.MONTANHAS, "DIR0301", "2026/2"].grades.av1 == Decimal("4.0")
    assert index[Brand.LITORAL, "DIR0301", "2026/2"].grades.av1 == Decimal("9.0")


def test_the_official_grade_comes_from_the_brand_of_the_exam() -> None:
    first = progress(Brand.MONTANHAS, "UniMontanhas:070793", "4.0")
    second = progress(Brand.LITORAL, "UniLitoral:010101", "9.0")
    records = OfficialGrades.records_by_class([first, second])
    official = OfficialGrades.of(exam(Brand.LITORAL), records, TODAY)
    assert official is not None
    assert official.value == Decimal("9.0")
    assert OfficialGrades.of(exam(Brand.SAO_PAULO), records, TODAY) is None
