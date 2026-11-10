import httpx
from dishka.integrations.fastapi import setup_dishka
from fastapi import FastAPI
from langchain_core.language_models import BaseChatModel

from api.bootstrap.settings import Settings
from api.domain.ports.rate_limit import RateLimiter
from api.infrastructure.tracing import Tracing
from api.persistence.core.database import Database
from api.presentation.http import auth, chat
from tests.doubles.doubles import DoubleContainers
from tests.integration.chat.scripted_doubles import doubles_with


class ChatApp:
    def __init__(
        self,
        database: Database,
        model: BaseChatModel,
        settings: Settings,
        tracing: Tracing | None = None,
        rate_limiter: RateLimiter | None = None,
    ) -> None:
        doubles = doubles_with(database, model, tracing, rate_limiter)
        self.application = FastAPI()
        self.application.include_router(auth.router)
        self.application.include_router(chat.router)
        setup_dishka(DoubleContainers.http(settings, doubles), self.application)

    def client(self) -> httpx.AsyncClient:
        transport = httpx.ASGITransport(app=self.application)
        return httpx.AsyncClient(transport=transport, base_url="http://api")
