from collections.abc import Mapping
from dataclasses import dataclass

from api.application.agent.tools.registry import RegisteredTool
from api.application.shared.page import PageRequest
from api.application.shared.tool_result import ToolResult
from api.persistence.core.database import Database
from api.persistence.identity.student_session_repository import StudentSessionRepository
from tests.integration.agent.invariant_json import Arguments, Output, ToolCall
from tests.integration.agent.invariant_support import ArgumentPool, Sweep
from tests.integration.support.owned import Owned, owned_by
from tests.integration.support.sql_oracle import SqlOracle
from tests.integration.support.student_scopes import StudentScopes

SMALL_PAGE = 3
LARGE_PAGE = 100


@dataclass(frozen=True, slots=True)
class Walk:
    small: tuple[Output, ...]
    large: tuple[Output, ...]


@dataclass(frozen=True, slots=True)
class SampledPerson:
    person_id: str
    owned: Owned
    pool: ArgumentPool
    calls: tuple[ToolCall, ...]
    walks: Mapping[str, Walk]


class SampleBuilder:
    def __init__(self, database: Database, factory: StudentScopes) -> None:
        self._database = database
        self._factory = factory

    async def person(self, person_id: str) -> SampledPerson:
        owned = await self._owned_of(person_id)
        tools = (await self._factory.for_person(person_id)).tools
        pool = await ArgumentPool.of(SqlOracle(), owned)
        walks = {
            tool.definition.name: await self._walk(tool, pool.base(tool))
            for tool in tools
            if "page" in set(Sweep.parameters_of(tool))
        }
        calls = tuple(await Sweep.run(tools, pool))
        return SampledPerson(person_id, owned, pool, calls, walks)

    async def _owned_of(self, person_id: str) -> Owned:
        session = await StudentSessionRepository(self._database).load(person_id)
        return await owned_by(self._database, session)

    @classmethod
    async def _walk(cls, tool: RegisteredTool, base: Arguments) -> Walk:
        return Walk(
            small=await cls._pages(tool, base, SMALL_PAGE),
            large=await cls._pages(tool, base, LARGE_PAGE),
        )

    @staticmethod
    async def _pages(tool: RegisteredTool, base: Arguments, limit: int) -> tuple[Output, ...]:
        pages: list[Output] = []
        offset: int | None = 0
        while offset is not None:
            result = await tool.handler(**base, page=PageRequest(offset=offset, limit=limit))
            pages.append(result.model_dump(mode="json", by_alias=True))
            page = result.page if isinstance(result, ToolResult) else None
            offset = page.next_offset if page else None
        return tuple(pages)
