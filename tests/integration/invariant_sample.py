from collections.abc import Mapping
from dataclasses import dataclass

from api.application.dto.tool_result import ToolResult
from api.application.page import PageRequest
from api.composition.student_tools_factory import StudentToolsFactory
from api.domain.session import StudentSession
from api.persistence.database import Database
from api.persistence.student_session_repository import StudentSessionRepository
from api.presentation.tools.registry import RegisteredTool
from tests.integration.invariant_json import Arguments, Output, ToolCall
from tests.integration.invariant_support import ArgumentPool, Sweep
from tests.integration.sql_oracle import SqlOracle

SMALL_PAGE = 3
LARGE_PAGE = 100


@dataclass(frozen=True, slots=True)
class Walk:
    small: tuple[Output, ...]
    large: tuple[Output, ...]


@dataclass(frozen=True, slots=True)
class SampledPerson:
    person_id: str
    session: StudentSession
    pool: ArgumentPool
    calls: tuple[ToolCall, ...]
    walks: Mapping[str, Walk]


class SampleBuilder:
    def __init__(self, database: Database, factory: StudentToolsFactory) -> None:
        self._database = database
        self._factory = factory

    async def person(self, person_id: str) -> SampledPerson:
        session = await StudentSessionRepository(self._database.db_session_factory).load(person_id)
        tools = (await self._factory.for_person(person_id)).tools
        pool = await ArgumentPool.of(SqlOracle(self._database), session)
        walks = {
            tool.definition.name: await self._walk(tool, pool.base(tool))
            for tool in tools
            if "page" in set(Sweep.parameters_of(tool))
        }
        calls = tuple(await Sweep.run(tools, pool))
        return SampledPerson(person_id, session, pool, calls, walks)

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
