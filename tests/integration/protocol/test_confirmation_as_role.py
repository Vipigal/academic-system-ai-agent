from collections.abc import AsyncIterator
from http import HTTPStatus

import pytest
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine
from sqlalchemy.pool import NullPool

from api.bootstrap.settings import Settings
from tests.integration.protocol.confirmation_app import ConfirmationApp, confirm, login
from tests.integration.protocol.rolled_back import RolledBackBank, rolled_back

STUDENT = "UniSaoPaulo:180017"
PERSON = "3000003"


@pytest.fixture
async def role_engine() -> AsyncIterator[AsyncEngine]:
    url = Settings.from_environment().database_url.get_secret_value()
    engine = create_async_engine(url, poolclass=NullPool)
    yield engine
    await engine.dispose()


@pytest.fixture
async def bank(role_engine: AsyncEngine) -> AsyncIterator[RolledBackBank]:
    async with rolled_back(role_engine, "SELECT 1") as rolled:
        yield rolled


async def test_the_role_login_alone_is_enough_to_confirm(bank: RolledBackBank) -> None:
    assert await bank.as_app("SELECT session_user") == "api"
    app = ConfirmationApp(bank.database)
    token = await app.proposal_of(PERSON, "GEN-090")
    async with app.client() as client:
        response = await confirm(client, await login(client, STUDENT), token)
    assert response.status_code == HTTPStatus.CREATED
