from api.composition.student_repositories import StudentRepositories
from api.composition.student_services import StudentServices
from api.composition.student_tools import StudentTools
from api.domain.ports.clock import Clock
from api.domain.session import StudentSession
from api.persistence.database import Database
from api.persistence.repository_adapter import RepositoryAdapter
from api.persistence.student_session_repository import StudentSessionRepository
from api.presentation.tools.registry import ToolRegistry


class StudentToolsFactory:
    def __init__(self, database: Database, clock: Clock) -> None:
        self._database = database
        self._clock = clock

    async def for_person(self, person_id: str) -> ToolRegistry:
        return (await self.tools_of(person_id)).registry()

    async def tools_of(self, person_id: str) -> StudentTools:
        return StudentTools.of(await self.services_of(person_id))

    async def services_of(self, person_id: str) -> StudentServices:
        repository = StudentSessionRepository(self._database.db_session_factory)
        return self.services_for(await repository.load(person_id))

    def services_for(self, session: StudentSession) -> StudentServices:
        adapter = RepositoryAdapter(self._database.db_session_factory, session)
        return StudentServices(StudentRepositories.of(adapter), self._clock)
