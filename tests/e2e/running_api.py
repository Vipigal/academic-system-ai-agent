import io
from collections.abc import Generator
from contextlib import contextmanager
from dataclasses import dataclass
from unittest.mock import patch

import httpx
from langchain_core.language_models import BaseChatModel

from api.bootstrap.agent_providers import AgentProviders
from api.bootstrap.app import ApiFactory
from api.bootstrap.settings import Settings
from tests.e2e.captured_log import capture_into, restored_logging
from tests.integration.protocol.rolled_back import RolledBackBank


@dataclass(frozen=True, slots=True)
class RunningApi:
    client: httpx.AsyncClient
    log: io.StringIO


@contextmanager
def running_api(
    bank: RolledBackBank, settings: Settings, model: BaseChatModel | None = None
) -> Generator[RunningApi]:
    chosen = model if model is not None else AgentProviders.chat_model(settings)
    with (
        restored_logging() as stream,
        patch("api.bootstrap.singletons.Database", return_value=bank.database),
        patch.object(AgentProviders, "chat_model", return_value=chosen),
    ):
        application = ApiFactory.create(settings)
        capture_into(stream)
        transport = httpx.ASGITransport(app=application)
        yield RunningApi(httpx.AsyncClient(transport=transport, base_url="http://api"), stream)
