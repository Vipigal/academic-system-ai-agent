from dishka import AsyncContainer

from api.application.agent.student_tools import StudentTools
from api.application.agent.tools.registry import ToolRegistry
from api.bootstrap.settings import Settings
from api.domain.identity.session import StudentSession
from api.domain.ports.clock import Clock
from api.domain.ports.protocol import ProposalSigner
from api.persistence.core.database import Database
from api.persistence.identity.student_session_repository import StudentSessionRepository
from evals.fixed_clock import FixedClock
from tests.doubles.doubles import DoubleContainers


class StudentScopes:
    def __init__(self, database: Database, signer: ProposalSigner) -> None:
        self._database = database
        self._container: AsyncContainer = DoubleContainers.students(
            Settings.from_environment(),
            {Database: database, Clock: FixedClock(), ProposalSigner: signer},
        )

    async def of_session[T](self, session: StudentSession, kind: type[T]) -> T:
        async with self._container(context={StudentSession: session}) as scope:
            return await scope.get(kind)

    async def of_person[T](self, person_id: str, kind: type[T]) -> T:
        session = await StudentSessionRepository(self._database).load(person_id)
        return await self.of_session(session, kind)

    async def for_person(self, person_id: str) -> ToolRegistry:
        return (await self.of_person(person_id, StudentTools)).registry()
