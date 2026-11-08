from dataclasses import dataclass
from typing import Self

from api.bootstrap.agent_providers import AgentProviders
from api.bootstrap.settings import Settings
from api.domain.ports.clock import Clock
from api.infrastructure.clock import SystemClock
from api.persistence.core.database import Database


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
            database=Database(settings.database_url.get_secret_value()),
            clock=chosen,
            agent=AgentProviders(settings, chosen),
        )

    async def dispose(self) -> None:
        await self.database.dispose()
