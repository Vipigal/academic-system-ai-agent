import logging
from typing import Protocol

from redis.exceptions import RedisError

from api.domain.rate_limit.decision import RateLimitDecision

logger = logging.getLogger(__name__)

SECONDS_PER_HOUR = 3600


class RedisPipeline(Protocol):
    def incr(self, name: str) -> object: ...

    def expire(self, name: str, time: int, *, nx: bool = ...) -> object: ...

    def ttl(self, name: str) -> object: ...

    async def execute(self) -> list[int]: ...


class RedisClient(Protocol):
    def pipeline(self, *, transaction: bool = ...) -> RedisPipeline: ...


class RedisRateLimiter:
    def __init__(
        self, client: RedisClient, limit: int, window_seconds: int = SECONDS_PER_HOUR
    ) -> None:
        self._client = client
        self._limit = limit
        self._window_seconds = window_seconds

    async def consume(self, key: str, /) -> RateLimitDecision:
        try:
            count, _, ttl = await self._counted(key)
        except RedisError, OSError:
            logger.exception("Rate limit indisponível, mensagem liberada")
            return RateLimitDecision.unmetered()
        return RateLimitDecision.counted(count, self._limit, ttl)

    async def _counted(self, key: str) -> list[int]:
        pipeline = self._client.pipeline(transaction=True)
        pipeline.incr(key)
        pipeline.expire(key, self._window_seconds, nx=True)
        pipeline.ttl(key)
        return await pipeline.execute()


class UnlimitedRateLimiter:
    async def consume(self, _key: str, /) -> RateLimitDecision:
        return RateLimitDecision.unmetered()
