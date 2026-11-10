import logging
from collections.abc import AsyncIterator

from dishka import Provider, Scope, provide
from redis.asyncio import Redis
from redis.asyncio.retry import Retry
from redis.backoff import NoBackoff

from api.bootstrap.settings import Settings
from api.domain.ports.rate_limit import RateLimiter
from api.infrastructure.rate_limiter import RedisRateLimiter, UnlimitedRateLimiter

logger = logging.getLogger(__name__)

REDIS_TIMEOUT_SECONDS = 0.1


class RateLimitProvider(Provider):
    scope = Scope.APP

    @provide
    async def limiter(self, settings: Settings) -> AsyncIterator[RateLimiter]:
        client = self.client_of(settings)
        if client is None:
            yield UnlimitedRateLimiter()
            return
        yield RedisRateLimiter(client, settings.chat_rate_limit_per_hour)
        await client.aclose()

    @staticmethod
    def client_of(settings: Settings) -> Redis | None:
        url = settings.redis_url.get_secret_value() if settings.redis_url else ""
        if not url:
            logger.warning("APP_REDIS_URL vazio: o rate limit do chat está desligado")
            return None
        return Redis.from_url(
            url,
            socket_timeout=REDIS_TIMEOUT_SECONDS,
            socket_connect_timeout=REDIS_TIMEOUT_SECONDS,
            retry=Retry(NoBackoff(), retries=0),
        )
