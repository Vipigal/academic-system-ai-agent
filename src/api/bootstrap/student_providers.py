from api.application.agent.student_tools import StudentTools
from api.application.agent.tools.registry import ToolRegistry
from api.bootstrap.student_services import StudentServices
from api.bootstrap.tool_providers import ToolProviders
from api.domain.identity.session import StudentSession
from api.domain.ports.clock import Clock
from api.domain.ports.identity import StudentSessionLoader
from api.persistence.core.database import Database
from api.persistence.core.repository_adapter import RepositoryAdapter
from api.persistence.identity.student_session_repository import StudentSessionRepository


class StudentProviders:
    def __init__(self, database: Database, clock: Clock) -> None:
        self._database = database
        self._clock = clock

    def session_loader(self) -> StudentSessionLoader:
        return StudentSessionRepository(self._database.db_session_factory)

    async def services_of(self, person_id: str) -> StudentServices:
        return self.services_for(await self.session_loader().load(person_id))

    def services_for(self, session: StudentSession) -> StudentServices:
        adapter = RepositoryAdapter(self._database.db_session_factory, session)
        return StudentServices(adapter, self._clock)

    async def tools_of(self, person_id: str) -> StudentTools:
        return ToolProviders.tools_for(await self.services_of(person_id))

    async def for_person(self, person_id: str) -> ToolRegistry:
        return (await self.tools_of(person_id)).registry()
