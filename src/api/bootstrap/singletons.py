from dataclasses import dataclass
from typing import Self

from api.bootstrap.agent_providers import AgentProviders
from api.bootstrap.settings import Settings
from api.domain.ports.clock import Clock
from api.infrastructure.clock import SystemClock
from api.persistence.core.database import Database, PoolConfig


@dataclass(frozen=True, slots=True)
class Singletons:
    settings: Settings
    database: Database
    clock: Clock
    agent: AgentProviders

    @classmethod
    def create(cls, settings: Settings, clock: Clock | None = None) -> Self:
        chosen = clock or SystemClock()
        return cls(
            settings=settings,
            database=Database(settings.database_url.get_secret_value(), cls._pool(settings)),
            clock=chosen,
            agent=AgentProviders(settings, chosen),
        )

    @staticmethod
    def _pool(settings: Settings) -> PoolConfig:
        return PoolConfig(
            size=settings.db_pool_size,
            max_overflow=settings.db_max_overflow,
            timeout_seconds=settings.db_pool_timeout_seconds,
        )

    async def dispose(self) -> None:
        await self.database.dispose()
