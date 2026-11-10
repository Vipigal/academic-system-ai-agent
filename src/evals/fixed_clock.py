from datetime import date, datetime

from dishka import Provider, Scope, provide

from api.domain.ports.clock import Clock
from api.domain.protocol.opening import BRASILIA

SNAPSHOT_DATE = date(2026, 10, 31)


class FixedClock:
    def __init__(self, today: date = SNAPSHOT_DATE) -> None:
        self._today = today

    def now(self) -> datetime:
        return datetime.combine(self._today, datetime.min.time(), BRASILIA)

    def today(self) -> date:
        return self._today


class SnapshotClock(Provider):
    scope = Scope.APP

    @provide(override=True)
    def clock(self) -> Clock:
        return FixedClock()
