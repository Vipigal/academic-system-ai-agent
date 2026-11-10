from api.bootstrap.settings import Settings
from api.persistence.core.database import Database, PoolConfig

TEST_POOL = PoolConfig(size=5, max_overflow=10, timeout_seconds=30)


def database_at(url: str) -> Database:
    return Database(url, TEST_POOL)


def application_database() -> Database:
    return database_at(Settings.from_environment().database_url.get_secret_value())
