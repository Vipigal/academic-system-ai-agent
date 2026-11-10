import io
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from dataclasses import dataclass

import httpx
from langchain_core.language_models import BaseChatModel

from api.bootstrap.app import ApiFactory
from api.bootstrap.settings import Settings
from api.persistence.core.database import Database
from tests.e2e.captured_log import capture_into, restored_logging
from tests.integration.protocol.rolled_back import RolledBackBank


@dataclass(frozen=True, slots=True)
class RunningApi:
    client: httpx.AsyncClient
    log: io.StringIO


@asynccontextmanager
async def running_api(
    bank: RolledBackBank, settings: Settings, model: BaseChatModel | None = None
) -> AsyncGenerator[RunningApi]:
    given: dict[object, object] = {Database: bank.database}
    if model is not None:
        given[BaseChatModel] = model
    with restored_logging() as stream:
        application = ApiFactory.create(settings, given)
        capture_into(stream)
        async with application.router.lifespan_context(application):
            transport = httpx.ASGITransport(app=application)
            yield RunningApi(httpx.AsyncClient(transport=transport, base_url="http://api"), stream)
