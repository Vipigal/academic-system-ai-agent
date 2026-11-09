import secrets
from collections.abc import Awaitable, Callable

import pytest

from api.application.agent.student_tools import StudentTools
from api.application.shared.page import PageRequest
from api.application.shared.tool_result import ToolResult
from api.bootstrap.student_providers import StudentProviders
from api.infrastructure.clock import FixedClock
from api.infrastructure.proposal_signer import ProposalJwtSigner
from api.persistence.core.database import Database

PAGE_SIZE = 100
SWEEP = pytest.mark.sweep
SLOW = pytest.mark.slow
SIGNER = ProposalJwtSigner(secrets.token_urlsafe(32), 15)


def tools_factory(database: Database) -> StudentProviders:
    return StudentProviders(database, FixedClock(), SIGNER)


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
