from collections.abc import Sequence
from dataclasses import dataclass

from pydantic import BaseModel, ConfigDict

DEFAULT_LIMIT = 20
MAX_LIMIT = 100


class PageInfo(BaseModel):
    model_config = ConfigDict(frozen=True)

    offset: int
    limit: int
    total: int
    next_offset: int | None


@dataclass(frozen=True, slots=True)
class Page[T]:
    items: tuple[T, ...]
    info: PageInfo


class PageRequest(BaseModel):
    model_config = ConfigDict(frozen=True)

    offset: int = 0
    limit: int = DEFAULT_LIMIT

    def paginate[T](self, items: Sequence[T]) -> Page[T]:
        offset = max(self.offset, 0)
        limit = min(max(self.limit, 1), MAX_LIMIT)
        end = offset + limit
        total = len(items)
        info = PageInfo(
            offset=offset,
            limit=limit,
            total=total,
            next_offset=end if end < total else None,
        )
        return Page(items=tuple(items[offset:end]), info=info)


FIRST_PAGE = PageRequest()
