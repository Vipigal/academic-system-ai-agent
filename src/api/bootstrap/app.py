from dishka import AsyncContainer
from dishka.integrations.fastapi import setup_dishka
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.bootstrap.containers import Containers
from api.bootstrap.lifespan import ContainerLifespan
from api.bootstrap.request_log import RequestLog
from api.bootstrap.routes import ApiRoutes
from api.bootstrap.settings import Settings
from api.infrastructure.logging import JsonLogging
from api.persistence.core.ownership_criteria import OwnershipRegistry

CORS_METHODS = ["GET", "POST", "OPTIONS"]
CORS_HEADERS = ["Authorization", "Content-Type"]
CORS_EXPOSED_HEADERS = ["Retry-After", "RateLimit-Limit", "RateLimit-Remaining", "RateLimit-Reset"]


class ApiFactory:
    @classmethod
    def create(cls) -> FastAPI:
        settings = Settings.from_environment()
        return cls.assemble(settings, Containers.http(settings))

    @staticmethod
    def assemble(settings: Settings, container: AsyncContainer) -> FastAPI:
        OwnershipRegistry.assert_complete()
        JsonLogging.configure()
        application = FastAPI(
            title="Agente de atendimento ao aluno", lifespan=ContainerLifespan(container)
        )
        application.add_middleware(
            CORSMiddleware,
            allow_origins=settings.cors_origins,
            allow_methods=CORS_METHODS,
            allow_headers=CORS_HEADERS,
            expose_headers=CORS_EXPOSED_HEADERS,
        )
        application.add_middleware(RequestLog)
        ApiRoutes.mount(application, settings)
        setup_dishka(container, application)
        return application
