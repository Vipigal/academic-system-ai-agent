import logging
from unittest.mock import AsyncMock, patch

import pytest
from pydantic import ValidationError
from redis.asyncio import Redis
from redis.asyncio.retry import Retry

from api.bootstrap.rate_limit_providers import REDIS_TIMEOUT_SECONDS, RateLimitProviders
from api.bootstrap.settings import Settings
from api.bootstrap.singletons import Singletons
from api.infrastructure.rate_limiter import RedisRateLimiter, UnlimitedRateLimiter

DATABASE_URL = "postgresql+asyncpg://api:api@127.0.0.1:5432/nada"
REDIS_URL = "redis://127.0.0.1:6379/0"


def settings_with(**overrides: object) -> Settings:
    return Settings.model_validate(
        {"database_url": DATABASE_URL, "agent_model": "fake", **overrides}
    )


@pytest.mark.parametrize("redis_url", [None, ""], ids=["absent", "empty"])
async def test_without_a_redis_url_the_chat_is_unlimited_and_the_startup_warns(
    redis_url: str | None, caplog: pytest.LogCaptureFixture
) -> None:
    with caplog.at_level(logging.WARNING, logger="api.bootstrap.rate_limit_providers"):
        singletons = Singletons.create(settings_with(redis_url=redis_url))

    assert isinstance(singletons.rate_limit.limiter, UnlimitedRateLimiter)
    assert ["APP_REDIS_URL" in record.getMessage() for record in caplog.records] == [True]
    await singletons.dispose()


async def test_with_a_redis_url_the_chat_counts_in_redis() -> None:
    singletons = Singletons.create(settings_with(redis_url=REDIS_URL))

    assert isinstance(singletons.rate_limit.limiter, RedisRateLimiter)
    await singletons.dispose()


async def test_the_redis_client_fails_fast_with_short_timeouts_and_no_retry() -> None:
    client = RateLimitProviders.client_of(settings_with(redis_url=REDIS_URL))

    assert client is not None
    options = client.connection_pool.connection_kwargs
    assert options["socket_timeout"] == REDIS_TIMEOUT_SECONDS
    assert options["socket_connect_timeout"] == REDIS_TIMEOUT_SECONDS
    assert isinstance(options["retry"], Retry)
    assert options["retry"].get_retries() == 0
    await client.aclose()


async def test_the_redis_client_closes_with_the_singletons() -> None:
    with patch.object(Redis, "aclose", new_callable=AsyncMock) as closed:
        singletons = Singletons.create(settings_with(redis_url=REDIS_URL))
        await singletons.dispose()

    closed.assert_awaited_once()


@pytest.mark.parametrize("limit", [0, -1], ids=["zero", "negative"])
def test_the_hourly_chat_limit_must_be_positive(limit: int) -> None:
    with pytest.raises(ValidationError, match="chat_rate_limit_per_hour"):
        settings_with(chat_rate_limit_per_hour=limit)
