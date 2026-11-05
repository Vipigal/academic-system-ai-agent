from collections.abc import Awaitable, Callable
from datetime import date

from api.application.dto.tool_result import ToolResult
from api.application.page import PageRequest
from api.composition.student_tools import StudentTools
from api.composition.student_tools_factory import StudentToolsFactory
from api.persistence.database import Database

REFERENCE = date(2026, 10, 31)
PAGE_SIZE = 100


class FixedClock:
    def __init__(self, today: date = REFERENCE) -> None:
        self._today = today

    def today(self) -> date:
        return self._today


def tools_factory(database: Database) -> StudentToolsFactory:
    return StudentToolsFactory(database, FixedClock())


async def student_tools(database: Database, person_id: str) -> StudentTools:
    return await tools_factory(database).tools_of(person_id)


type PageCall[T] = Callable[[PageRequest], Awaitable[ToolResult[list[T]]]]


async def all_pages[T](call: PageCall[T], limit: int = PAGE_SIZE) -> list[T]:
    items: list[T] = []
    offset: int | None = 0
    while offset is not None:
        result = await call(PageRequest(offset=offset, limit=limit))
        items.extend(result.data or [])
        offset = result.page.next_offset if result.page else None
    return items
