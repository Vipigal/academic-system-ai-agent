from langchain_core.language_models import BaseChatModel

from api.domain.ports.clock import Clock
from api.domain.ports.rate_limit import RateLimiter
from api.infrastructure.rate_limiter import UnlimitedRateLimiter
from api.infrastructure.tracing import Tracing
from api.persistence.core.database import Database
from evals.fixed_clock import FixedClock


def doubles_with(
    database: Database,
    model: BaseChatModel,
    tracing: Tracing | None = None,
    rate_limiter: RateLimiter | None = None,
) -> dict[type, object]:
    return {
        Database: database,
        BaseChatModel: model,
        Clock: FixedClock(),
        Tracing: tracing or Tracing(None, None, None, None),
        RateLimiter: rate_limiter or UnlimitedRateLimiter(),
    }
