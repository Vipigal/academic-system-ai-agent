from typing import Protocol

from api.domain.rate_limit.decision import RateLimitDecision


class RateLimiter(Protocol):
    async def consume(self, key: str, /) -> RateLimitDecision: ...
