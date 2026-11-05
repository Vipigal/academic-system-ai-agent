from collections.abc import AsyncIterator

import pytest

from api.persistence.database import Database
from api.settings import Settings


@pytest.fixture
async def database() -> AsyncIterator[Database]:
    connected = Database(Settings.from_environment().database_url.get_secret_value())
    yield connected
    await connected.dispose()
