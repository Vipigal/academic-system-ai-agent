import time
from datetime import date, datetime, timedelta

from api.domain.protocol.opening import BRASILIA
from api.infrastructure.clock import SystemClock
from evals.fixed_clock import FixedClock

TOLERANCE = timedelta(seconds=5)


def test_the_system_clock_reads_the_real_instant_in_brasilia() -> None:
    clock = SystemClock()

    now = clock.now()

    assert now.utcoffset() == timedelta(hours=-3)
    assert abs(now - datetime.fromtimestamp(time.time(), BRASILIA)) < TOLERANCE
    assert clock.today() in {now.date(), now.date() + timedelta(days=1)}


def test_the_fixed_clock_is_the_snapshot_day_of_the_data() -> None:
    clock = FixedClock()

    assert clock.today() == date(2026, 10, 31)
    assert clock.now() == datetime(2026, 10, 31, tzinfo=BRASILIA)


def test_the_fixed_clock_takes_another_day() -> None:
    clock = FixedClock(date(2026, 1, 2))

    assert (clock.today(), clock.now().date()) == (date(2026, 1, 2), date(2026, 1, 2))
