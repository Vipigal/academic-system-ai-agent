import asyncio
from collections.abc import Sequence

from api.domain.lms import OnlineExam
from api.domain.lms_account import LmsAccount
from api.domain.lms_material import CourseMaterial
from api.persistence.lms.account_mapper import AccountMapper
from api.persistence.lms.exam_mapper import ExamMapper, ExamSources
from api.persistence.lms.lms_queries import LmsBaseQueries, LmsQueries
from api.persistence.lms.material_mapper import MaterialMapper, MaterialSources
from api.persistence.repository_adapter import RepositoryAdapter


class SqlLmsRepository:
    def __init__(self, adapter: RepositoryAdapter) -> None:
        self._adapter = adapter

    async def list_exams(self) -> Sequence[OnlineExam]:
        courses = await self._course_ids()
        found, quizzes, attempts, subjects = await asyncio.gather(
            self._adapter.fetch(LmsQueries.courses(courses)),
            self._adapter.fetch(LmsQueries.quizzes(courses)),
            self._adapter.fetch(LmsBaseQueries.attempts()),
            self._adapter.fetch(LmsBaseQueries.subjects()),
        )
        return ExamMapper.to_entities(ExamSources(found, quizzes, attempts, subjects))

    async def list_accounts(self) -> Sequence[LmsAccount]:
        users = await self._adapter.fetch(LmsBaseQueries.users())
        return AccountMapper.to_entities(users, self._adapter.student_session.enrollment_keys)

    async def list_materials(self) -> Sequence[CourseMaterial]:
        courses = await self._course_ids()
        found, modules, views, subjects = await asyncio.gather(
            self._adapter.fetch(LmsQueries.courses(courses)),
            self._adapter.fetch(LmsQueries.modules(courses)),
            self._adapter.fetch(LmsQueries.views(courses)),
            self._adapter.fetch(LmsBaseQueries.subjects()),
        )
        return MaterialMapper.to_entities(MaterialSources(found, modules, views, subjects))

    async def _course_ids(self) -> set[str]:
        enrolments = await self._adapter.fetch(LmsBaseQueries.enrolments())
        return {row.course_id for row in enrolments}
