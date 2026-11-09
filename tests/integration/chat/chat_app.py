import httpx
from fastapi import FastAPI
from langchain_core.language_models import BaseChatModel

from api.bootstrap.chat_agent_scope import ChatAgentScope
from api.bootstrap.chat_providers import ChatProviders
from api.bootstrap.identity_providers import IdentityProviders
from api.bootstrap.settings import Settings
from api.domain.ports.rate_limit import RateLimiter
from api.infrastructure.tracing import Tracing
from api.persistence.core.database import Database
from tests.integration.chat.scripted_singletons import singletons_with


class ChatApp:
    def __init__(
        self,
        database: Database,
        model: BaseChatModel,
        settings: Settings,
        tracing: Tracing | None = None,
        rate_limiter: RateLimiter | None = None,
    ) -> None:
        singletons = singletons_with(database, model, settings, rate_limiter)
        identity = IdentityProviders(settings, database)
        scope = ChatAgentScope(singletons, tracing or Tracing(None, None, None, None))
        self.application = FastAPI()
        login = identity.auth_router()
        assert login is not None
        self.application.include_router(login)
        self.application.include_router(ChatProviders(singletons, scope, identity).router())

    def client(self) -> httpx.AsyncClient:
        transport = httpx.ASGITransport(app=self.application)
        return httpx.AsyncClient(transport=transport, base_url="http://api")
