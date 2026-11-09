from collections.abc import Collection

from sqlalchemy import Select, select

from api.persistence.lms.models import (
    LmsCourseModuleRow,
    LmsCourseRow,
    LmsEnrolmentRow,
    LmsLogRow,
    LmsQuizAttemptRow,
    LmsQuizRow,
    LmsUserRow,
)
from api.persistence.lms.vocabulary import MATERIAL_KIND_BY_SOURCE, VIEW_EVENTS
from api.persistence.sag.catalog_models import SubjectRow


class LmsBaseQueries:
    @staticmethod
    def users() -> Select[LmsUserRow]:
        return select(LmsUserRow)

    @staticmethod
    def enrolments() -> Select[LmsEnrolmentRow]:
        return select(LmsEnrolmentRow)

    @staticmethod
    def attempts() -> Select[LmsQuizAttemptRow]:
        return select(LmsQuizAttemptRow)

    @staticmethod
    def subjects() -> Select[SubjectRow]:
        return select(SubjectRow)


class LmsQueries:
    @staticmethod
    def courses(courses: Collection[str]) -> Select[LmsCourseRow]:
        return select(LmsCourseRow).where(LmsCourseRow.id.in_(courses))

    @staticmethod
    def quizzes(courses: Collection[str]) -> Select[LmsQuizRow]:
        return select(LmsQuizRow).where(LmsQuizRow.course_id.in_(courses))

    @staticmethod
    def modules(courses: Collection[str]) -> Select[LmsCourseModuleRow]:
        return select(LmsCourseModuleRow).where(
            LmsCourseModuleRow.course_id.in_(courses),
            LmsCourseModuleRow.kind.in_(list(MATERIAL_KIND_BY_SOURCE)),
        )

    @staticmethod
    def views(courses: Collection[str]) -> Select[LmsLogRow]:
        return (
            select(LmsLogRow)
            .join(LmsCourseModuleRow, LmsLogRow.module_id == LmsCourseModuleRow.id)
            .where(
                LmsCourseModuleRow.course_id.in_(courses),
                LmsCourseModuleRow.kind.in_(list(MATERIAL_KIND_BY_SOURCE)),
                LmsLogRow.event_name.in_(VIEW_EVENTS),
            )
        )
