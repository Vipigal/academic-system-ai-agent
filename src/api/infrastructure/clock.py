import time
from datetime import date, datetime

from api.domain.protocol.opening import BRASILIA


class SystemClock:
    def now(self) -> datetime:
        return datetime.fromtimestamp(time.time(), BRASILIA)

    def today(self) -> date:
        return self.now().date()
