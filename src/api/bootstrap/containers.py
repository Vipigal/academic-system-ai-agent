from dishka import AsyncContainer, Provider, Scope, make_async_container

from api.bootstrap.agent_providers import AgentProvider
from api.bootstrap.app_provider import AppProvider
from api.bootstrap.chat_providers import ChatProvider
from api.bootstrap.identity_providers import IdentityProvider
from api.bootstrap.protocol_confirmation_providers import ProtocolConfirmationProvider
from api.bootstrap.protocol_providers import ProtocolProvider
from api.bootstrap.rate_limit_providers import RateLimitProvider
from api.bootstrap.session_providers import GivenSession, HttpSession
from api.bootstrap.settings import Settings
from api.bootstrap.student_providers import StudentProvider
from api.bootstrap.tool_providers import ToolProvider

type Given = dict[object, object]


class GivenObjects(Provider):
    def __init__(self, given: Given) -> None:
        super().__init__(scope=Scope.APP)
        for kind in given:
            self.from_context(provides=kind, override=True)


class Containers:
    @classmethod
    def http(cls, settings: Settings, given: Given | None = None) -> AsyncContainer:
        return cls._create(settings, given or {}, HttpSession())

    @classmethod
    def students(cls, settings: Settings, given: Given | None = None) -> AsyncContainer:
        return cls._create(settings, given or {}, GivenSession())

    @staticmethod
    def _create(settings: Settings, given: Given, session: Provider) -> AsyncContainer:
        return make_async_container(
            AppProvider(),
            AgentProvider(),
            RateLimitProvider(),
            IdentityProvider(),
            StudentProvider(),
            ToolProvider(),
            ProtocolProvider(),
            ProtocolConfirmationProvider(),
            ChatProvider(),
            session,
            GivenObjects(given),
            context={Settings: settings, **given},
        )
