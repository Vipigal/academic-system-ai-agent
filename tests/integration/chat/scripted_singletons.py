from unittest.mock import patch

from langchain_core.language_models import BaseChatModel

from api.bootstrap.agent_providers import AgentProviders
from api.bootstrap.settings import Settings
from api.bootstrap.singletons import Singletons
from api.persistence.core.database import Database
from tests.integration.support.tools import FixedClock


def singletons_with(database: Database, model: BaseChatModel, settings: Settings) -> Singletons:
    clock = FixedClock()
    agent = AgentProviders(settings, clock)
    with patch.object(AgentProviders, "chat_model", return_value=model):
        assert agent.runtime.model is model
    return Singletons(settings, database, clock, agent)
