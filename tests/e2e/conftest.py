from collections.abc import AsyncIterator

import pytest

from tests.integration.protocol.rolled_back import RolledBackBank, rolled_back
from tests.integration.support.sql_oracle import admin_engine


@pytest.fixture
async def bank() -> AsyncIterator[RolledBackBank]:
    async with rolled_back(admin_engine(), "SET LOCAL ROLE api") as rolled:
        yield rolled
