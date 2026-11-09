from api.domain.identity.session import StudentSession
from api.domain.ports.rate_limit import RateLimiter
from api.domain.rate_limit.chat_key import ChatRateLimitKey
from api.domain.rate_limit.decision import RateLimitDecision


class ChatRateLimit:
    def __init__(self, session: StudentSession, limiter: RateLimiter) -> None:
        self._session = session
        self._limiter = limiter

    async def admit(self) -> RateLimitDecision:
        return await self._limiter.consume(ChatRateLimitKey.of(self._session))
