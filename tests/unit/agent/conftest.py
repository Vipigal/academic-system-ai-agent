from collections.abc import AsyncIterator

import pytest
from dishka import AsyncContainer
from langchain_core.language_models import BaseChatModel

from api.bootstrap.settings import Settings
from api.domain.ports.clock import Clock
from evals.fixed_clock import FixedClock
from tests.doubles.doubles import DoubleContainers
from tests.doubles.scripted_model import ScriptedChatModel

DATABASE_URL = "postgresql+asyncpg://api:api@127.0.0.1:5432/nada"


@pytest.fixture
async def dated_container() -> AsyncIterator[AsyncContainer]:
    settings = Settings.model_validate({"database_url": DATABASE_URL, "agent_model": "fake"})
    doubles = {Clock: FixedClock(), BaseChatModel: ScriptedChatModel.standard()}
    container = DoubleContainers.http(settings, doubles)
    yield container
    await container.close()
