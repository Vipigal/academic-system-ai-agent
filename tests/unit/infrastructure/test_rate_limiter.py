import logging

import pytest
from redis.exceptions import ConnectionError as RedisConnectionError

from api.domain.rate_limit.decision import RateLimitDecision
from api.infrastructure.rate_limiter import RedisRateLimiter, UnlimitedRateLimiter
from tests.unit.infrastructure.memory_redis import MemoryRedis

KEY = "ratelimit:chat:3000003"
HOUR = 3600


async def consumed(limiter: RedisRateLimiter, times: int) -> list[RateLimitDecision]:
    return [await limiter.consume(KEY) for _ in range(times)]


async def last_of(limiter: RedisRateLimiter, times: int = 1) -> RateLimitDecision:
    return (await consumed(limiter, times))[-1]


async def test_each_message_counts_until_the_limit_and_the_next_is_denied() -> None:
    limiter = RedisRateLimiter(MemoryRedis(), limit=2)

    decisions = await consumed(limiter, 3)

    assert [(item.allowed, item.remaining) for item in decisions] == [
        (True, 1),
        (True, 0),
        (False, 0),
    ]
    assert {item.limit for item in decisions} == {2}


async def test_the_denial_says_how_long_until_the_window_ends() -> None:
    store = MemoryRedis()
    limiter = RedisRateLimiter(store, limit=1)
    await consumed(limiter, 1)
    store.advance(1000)

    denied = await last_of(limiter)

    assert not denied.allowed
    assert denied.reset_after_seconds == HOUR - 1000


async def test_the_first_message_opens_a_window_of_one_hour() -> None:
    store = MemoryRedis()

    first = await last_of(RedisRateLimiter(store, limit=5))

    assert first.reset_after_seconds == HOUR
    assert store.ttl(KEY) == HOUR


async def test_later_messages_keep_the_window_of_the_first() -> None:
    store = MemoryRedis()
    limiter = RedisRateLimiter(store, limit=5)
    await consumed(limiter, 1)
    store.advance(100)

    later = await last_of(limiter)

    assert later.reset_after_seconds == HOUR - 100
    assert store.ttl(KEY) == HOUR - 100


async def test_when_the_window_ends_the_count_starts_again() -> None:
    store = MemoryRedis()
    limiter = RedisRateLimiter(store, limit=1)
    await consumed(limiter, 2)
    store.advance(HOUR)

    renewed = await last_of(limiter)

    assert (renewed.allowed, renewed.remaining, renewed.reset_after_seconds) == (True, 0, HOUR)


async def test_each_person_has_a_count_of_their_own() -> None:
    limiter = RedisRateLimiter(MemoryRedis(), limit=1)
    await consumed(limiter, 1)

    other = await limiter.consume("ratelimit:chat:3000004")

    assert other.allowed


@pytest.mark.parametrize(
    "failure",
    [RedisConnectionError("Connection refused"), TimeoutError()],
    ids=["unreachable", "slow"],
)
async def test_without_redis_the_message_passes_and_the_error_is_logged(
    failure: Exception, caplog: pytest.LogCaptureFixture
) -> None:
    limiter = RedisRateLimiter(MemoryRedis(failure=failure), limit=1)

    with caplog.at_level(logging.ERROR, logger="api.infrastructure.rate_limiter"):
        decisions = await consumed(limiter, 2)

    assert decisions == [RateLimitDecision.unmetered()] * 2
    assert [record.exc_info and record.exc_info[1] for record in caplog.records] == [failure] * 2


async def test_without_a_redis_url_every_message_passes_unmetered() -> None:
    limiter = UnlimitedRateLimiter()

    assert await limiter.consume(KEY) == RateLimitDecision.unmetered()
