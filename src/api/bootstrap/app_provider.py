from collections.abc import AsyncIterator, Iterator

from dishka import Provider, Scope, alias, from_context, provide

from api.application.health.service import HealthService
from api.bootstrap.observability import Observability
from api.bootstrap.settings import Settings
from api.domain.ports.clock import Clock
from api.domain.ports.health import DatabaseProbe
from api.domain.ports.tracing import TraceLog
from api.infrastructure.clock import SystemClock
from api.infrastructure.tracing import CurrentTrace, Tracing
from api.persistence.core.database import Database, PoolConfig


class AppProvider(Provider):
    scope = Scope.APP

    settings = from_context(provides=Settings)
    clock = provide(SystemClock, provides=Clock)
    probe = alias(source=Database, provides=DatabaseProbe)
    health = provide(HealthService)

    @provide
    async def database(self, settings: Settings) -> AsyncIterator[Database]:
        pool = PoolConfig(
            size=settings.db_pool_size,
            max_overflow=settings.db_max_overflow,
            timeout_seconds=settings.db_pool_timeout_seconds,
        )
        database = Database(settings.database_url.get_secret_value(), pool)
        yield database
        await database.dispose()

    @provide
    def tracing(self, settings: Settings) -> Iterator[Tracing]:
        tracing = Observability.start(settings)
        yield tracing
        tracing.shutdown()

    @provide
    def trace_log(self, tracing: Tracing) -> TraceLog:
        return CurrentTrace(enabled=tracing.enabled)
