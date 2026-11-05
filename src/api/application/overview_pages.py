from collections.abc import Awaitable, Callable

from api.application.dto.tool_result import Caveat, ToolResult
from api.application.page import MAX_LIMIT, PageRequest

type Listing[T] = ToolResult[list[T]]
type PageCall[T] = Callable[[PageRequest], Awaitable[ToolResult[list[T]]]]


class Gathered[T]:
    def __init__(self, items: list[T], caveats: tuple[Caveat, ...]) -> None:
        self.items = items
        self.caveats = caveats

    @staticmethod
    async def of_pages[I](call: PageCall[I]) -> Gathered[I]:
        items: list[I] = []
        caveats: tuple[Caveat, ...] = ()
        offset: int | None = 0
        while offset is not None:
            result = await call(PageRequest(offset=offset, limit=MAX_LIMIT))
            items.extend(result.data or [])
            caveats = result.caveats
            offset = result.page.next_offset if result.page else None
        return Gathered(items, caveats)

    @staticmethod
    def of_result[I](result: ToolResult[list[I]]) -> Gathered[I]:
        return Gathered(result.data or [], result.caveats)
