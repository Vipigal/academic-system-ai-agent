import pytest
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine

from api.bootstrap.settings import Settings
from api.bootstrap.singletons import Singletons
from api.persistence.core import database
from api.persistence.core.database import Database

DATABASE_URL = "postgresql+asyncpg://api:api@127.0.0.1:5432/nada"


class EngineSpy:
    def __init__(self) -> None:
        self.options: dict[str, object] = {}

    def __call__(self, url: str, **options: object) -> AsyncEngine:
        self.options = options
        return create_async_engine(url, **options)


@pytest.fixture
def engine_spy(monkeypatch: pytest.MonkeyPatch) -> EngineSpy:
    spy = EngineSpy()
    monkeypatch.setattr(database, "create_async_engine", spy)
    return spy


async def test_the_engine_pool_comes_from_the_settings(engine_spy: EngineSpy) -> None:
    settings = Settings.model_validate(
        {
            "database_url": DATABASE_URL,
            "agent_model": "fake",
            "db_pool_size": 7,
            "db_max_overflow": 3,
            "db_pool_timeout_seconds": 2.5,
        }
    )

    singletons = Singletons.create(settings)

    assert engine_spy.options["pool_size"] == 7
    assert engine_spy.options["max_overflow"] == 3
    assert engine_spy.options["pool_timeout"] == 2.5
    assert engine_spy.options["pool_pre_ping"] is True
    await singletons.dispose()


async def test_without_a_pool_the_engine_keeps_the_sqlalchemy_defaults(
    engine_spy: EngineSpy,
) -> None:
    connected = Database(DATABASE_URL)

    assert set(engine_spy.options) == {"connect_args", "hide_parameters"}
    await connected.dispose()
