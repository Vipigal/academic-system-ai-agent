from unittest.mock import patch

from langchain_core.language_models import BaseChatModel

from api.bootstrap.agent_providers import AgentProviders
from api.bootstrap.rate_limit_providers import RateLimitProviders
from api.bootstrap.settings import Settings
from api.bootstrap.singletons import Singletons
from api.domain.ports.rate_limit import RateLimiter
from api.infrastructure.clock import FixedClock
from api.infrastructure.rate_limiter import UnlimitedRateLimiter
from api.persistence.core.database import Database


def singletons_with(
    database: Database,
    model: BaseChatModel,
    settings: Settings,
    rate_limiter: RateLimiter | None = None,
) -> Singletons:
    clock = FixedClock()
    agent = AgentProviders(settings, clock)
    with patch.object(AgentProviders, "chat_model", return_value=model):
        assert agent.runtime.model is model
    rate_limit = RateLimitProviders(rate_limiter or UnlimitedRateLimiter())
    return Singletons(settings, database, clock, agent, rate_limit)
