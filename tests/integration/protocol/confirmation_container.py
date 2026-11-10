from dishka import AsyncContainer

from api.bootstrap.containers import Containers
from api.bootstrap.settings import Settings
from api.domain.ports.clock import Clock
from api.infrastructure.clock import FixedClock
from api.infrastructure.tracing import Tracing
from api.persistence.core.database import Database


def confirmation_container(database: Database, settings: Settings) -> AsyncContainer:
    untraced = Tracing(None, None, None, None)
    given: dict[object, object] = {Database: database, Clock: FixedClock(), Tracing: untraced}
    return Containers.http(settings, given)
