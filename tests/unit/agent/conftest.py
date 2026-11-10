from collections.abc import AsyncIterator

import pytest
from dishka import AsyncContainer

from api.bootstrap.containers import Containers
from api.bootstrap.settings import Settings
from api.domain.ports.clock import Clock
from api.infrastructure.clock import FixedClock

DATABASE_URL = "postgresql+asyncpg://api:api@127.0.0.1:5432/nada"


@pytest.fixture
async def dated_container() -> AsyncIterator[AsyncContainer]:
    settings = Settings.model_validate({"database_url": DATABASE_URL, "agent_model": "fake"})
    container = Containers.http(settings, {Clock: FixedClock()})
    yield container
    await container.close()
