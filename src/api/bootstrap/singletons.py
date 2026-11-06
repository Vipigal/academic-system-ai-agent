from dataclasses import dataclass
from typing import Self

from api.bootstrap.settings import Settings
from api.domain.ports.clock import Clock
from api.infrastructure.clock import ReferenceClock
from api.persistence.core.database import Database


@dataclass(frozen=True, slots=True)
class Singletons:
    settings: Settings
    database: Database
    clock: Clock

    @classmethod
    def create(cls, settings: Settings) -> Self:
        return cls(
            settings=settings,
            database=Database(settings.database_url.get_secret_value()),
            clock=ReferenceClock(settings.reference_date),
        )

    async def dispose(self) -> None:
        await self.database.dispose()
