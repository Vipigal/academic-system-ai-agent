from collections.abc import Sequence
from typing import Protocol

from api.domain.academic.curriculum import EnrollmentProgress
from api.domain.academic.enrollment import CourseOffer, Enrollment, SubjectTeacher
from api.domain.academic.term_calendar import AcademicCalendar


class AcademicCatalogRepository(Protocol):
    async def get_calendar(self) -> AcademicCalendar: ...

    async def list_course_offers(self) -> Sequence[CourseOffer]: ...

    async def list_subject_teachers(
        self, subject_code: str, term: str
    ) -> Sequence[SubjectTeacher]: ...


class StudentAcademicRepository(Protocol):
    async def list_enrollments(self) -> Sequence[Enrollment]: ...

    async def list_progress(self) -> Sequence[EnrollmentProgress]: ...
