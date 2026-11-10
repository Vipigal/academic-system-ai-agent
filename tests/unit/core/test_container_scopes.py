import asyncio
from dataclasses import dataclass

from dishka import AsyncContainer

from api.application.agent.student_tools import StudentTools
from api.application.finance.service import FinancialService
from api.bootstrap.containers import Containers
from api.bootstrap.settings import Settings
from api.domain.identity.session import StudentSession
from api.persistence.core.database import Database
from api.persistence.core.repository_adapter import RepositoryAdapter

SETTINGS = Settings.model_validate(
    {
        "database_url": "postgresql+asyncpg://nobody:nothing@127.0.0.1:1/nothing",
        "agent_model": "fake",
        "proposal_secret": "segredo-de-teste-com-tamanho-suficiente",
    }
)
FIRST = StudentSession(person_ids=frozenset({"1"}), cpf="1", enrollment_keys=frozenset())
SECOND = StudentSession(person_ids=frozenset({"2"}), cpf="2", enrollment_keys=frozenset())


@dataclass(frozen=True, slots=True)
class Resolved:
    session: StudentSession
    adapter: RepositoryAdapter
    financial: FinancialService
    tools: StudentTools
    database: Database


async def resolved_for(container: AsyncContainer, session: StudentSession) -> Resolved:
    async with container(context={StudentSession: session}) as scope:
        await asyncio.sleep(0)
        services = await asyncio.gather(scope.get(FinancialService), scope.get(StudentTools))
        return Resolved(
            await scope.get(StudentSession),
            await scope.get(RepositoryAdapter),
            *services,
            await scope.get(Database),
        )


async def test_concurrent_request_scopes_share_the_database_and_nothing_of_the_student() -> None:
    container = Containers.students(SETTINGS)
    try:
        first, second = await asyncio.gather(
            resolved_for(container, FIRST), resolved_for(container, SECOND)
        )
    finally:
        await container.close()

    assert (first.session, second.session) == (FIRST, SECOND)
    assert (first.adapter.student_session, second.adapter.student_session) == (FIRST, SECOND)
    assert not {first.adapter, first.financial, first.tools} & {
        second.adapter,
        second.financial,
        second.tools,
    }
    assert first.database is second.database
