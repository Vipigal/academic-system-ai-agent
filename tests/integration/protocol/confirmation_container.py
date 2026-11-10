from dishka import AsyncContainer

from api.bootstrap.settings import Settings
from api.domain.ports.clock import Clock
from api.infrastructure.tracing import Tracing
from api.persistence.core.database import Database
from evals.fixed_clock import FixedClock
from tests.doubles.doubles import DoubleContainers


def confirmation_container(database: Database, settings: Settings) -> AsyncContainer:
    untraced = Tracing(None, None, None, None)
    given: dict[object, object] = {Database: database, Clock: FixedClock(), Tracing: untraced}
    return DoubleContainers.http(settings, given)
