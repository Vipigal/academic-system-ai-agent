import time
from datetime import date, datetime

from api.domain.protocol.opening import BRASILIA

SNAPSHOT_DATE = date(2026, 10, 31)


class SystemClock:
    def now(self) -> datetime:
        return datetime.fromtimestamp(time.time(), BRASILIA)

    def today(self) -> date:
        return self.now().date()


class FixedClock:
    def __init__(self, today: date = SNAPSHOT_DATE) -> None:
        self._today = today

    def now(self) -> datetime:
        return datetime.combine(self._today, datetime.min.time(), BRASILIA)

    def today(self) -> date:
        return self._today
