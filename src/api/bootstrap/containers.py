from dishka import AsyncContainer, Provider, make_async_container

from api.bootstrap.agent_providers import AgentProvider
from api.bootstrap.app_provider import AppProvider
from api.bootstrap.chat_providers import ChatProvider
from api.bootstrap.identity_providers import IdentityProvider
from api.bootstrap.protocol_confirmation_providers import ProtocolConfirmationProvider
from api.bootstrap.protocol_providers import ProtocolProvider
from api.bootstrap.rate_limit_providers import RateLimitProvider
from api.bootstrap.session_providers import HttpSession
from api.bootstrap.settings import Settings
from api.bootstrap.student_providers import StudentProvider
from api.bootstrap.tool_providers import ToolProvider

PROVIDERS = (
    AppProvider,
    AgentProvider,
    RateLimitProvider,
    IdentityProvider,
    StudentProvider,
    ToolProvider,
    ProtocolProvider,
    ProtocolConfirmationProvider,
    ChatProvider,
)


class Containers:
    @staticmethod
    def graph() -> tuple[Provider, ...]:
        return tuple(provider() for provider in PROVIDERS)

    @classmethod
    def http(cls, settings: Settings) -> AsyncContainer:
        return make_async_container(*cls.graph(), HttpSession(), context={Settings: settings})
