from fastapi import FastAPI

from api.bootstrap.settings import Settings
from api.presentation.http import auth, chat, health, protocol_confirmation


class ApiRoutes:
    @staticmethod
    def mount(application: FastAPI, settings: Settings) -> None:
        application.include_router(health.router)
        if settings.dev_login:
            application.include_router(auth.router)
        application.include_router(chat.router)
        application.include_router(protocol_confirmation.router)
