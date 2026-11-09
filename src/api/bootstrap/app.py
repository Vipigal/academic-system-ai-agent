from dishka.integrations.fastapi import setup_dishka
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.bootstrap.containers import Containers, Given
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
    @staticmethod
    def create(settings: Settings | None = None, given: Given | None = None) -> FastAPI:
        OwnershipRegistry.assert_complete()
        chosen = settings or Settings.from_environment()
        JsonLogging.configure()
        container = Containers.http(chosen, given)
        application = FastAPI(
            title="Agente de atendimento ao aluno", lifespan=ContainerLifespan(container)
        )
        application.add_middleware(
            CORSMiddleware,
            allow_origins=chosen.cors_origins,
            allow_methods=CORS_METHODS,
            allow_headers=CORS_HEADERS,
            expose_headers=CORS_EXPOSED_HEADERS,
        )
        application.add_middleware(RequestLog)
        ApiRoutes.mount(application, chosen)
        setup_dishka(container, application)
        return application
