import logging
from collections.abc import Awaitable, Callable
from typing import Annotated, Self

from fastapi import Depends
from redis.asyncio import Redis
from redis.asyncio.retry import Retry
from redis.backoff import NoBackoff

from api.application.chat.rate_limit import ChatRateLimit
from api.bootstrap.settings import Settings
from api.domain.identity.session import StudentSession
from api.domain.ports.rate_limit import RateLimiter
from api.infrastructure.rate_limiter import RedisRateLimiter, UnlimitedRateLimiter

logger = logging.getLogger(__name__)

REDIS_TIMEOUT_SECONDS = 0.1


class RateLimitProviders:
    def __init__(self, limiter: RateLimiter, client: Redis | None = None) -> None:
        self._limiter = limiter
        self._client = client

    @classmethod
    def create(cls, settings: Settings) -> Self:
        client = cls.client_of(settings)
        if client is None:
            return cls(UnlimitedRateLimiter())
        return cls(RedisRateLimiter(client, settings.chat_rate_limit_per_hour), client)

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

    @property
    def limiter(self) -> RateLimiter:
        return self._limiter

    def chat_dependency(
        self, session_dependency: Callable[..., Awaitable[StudentSession]]
    ) -> Callable[..., Awaitable[ChatRateLimit]]:
        async def chat_rate_limit(
            session: Annotated[StudentSession, Depends(session_dependency)],
        ) -> ChatRateLimit:
            return ChatRateLimit(session, self._limiter)

        return chat_rate_limit

    async def aclose(self) -> None:
        if self._client is not None:
            await self._client.aclose()
