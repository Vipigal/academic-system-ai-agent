from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.application.health.service import HealthService
from api.bootstrap.observability import Observability
from api.bootstrap.request_log import RequestLog
from api.bootstrap.settings import Settings
from api.bootstrap.singletons import Singletons
from api.bootstrap.student_routes import StudentRoutes
from api.persistence.core.ownership_criteria import OwnershipRegistry
from api.presentation.http.health import HealthRouter

CORS_METHODS = ["GET", "POST", "OPTIONS"]
CORS_HEADERS = ["Authorization", "Content-Type"]
CORS_EXPOSED_HEADERS = ["Retry-After", "RateLimit-Limit", "RateLimit-Remaining", "RateLimit-Reset"]


class ApiFactory:
    @staticmethod
    def create(settings: Settings | None = None) -> FastAPI:
        OwnershipRegistry.assert_complete()
        chosen = settings or Settings.from_environment()
        tracing = Observability.start(chosen)
        singletons = Singletons.create(chosen)

        @asynccontextmanager
        async def lifespan(_: FastAPI) -> AsyncGenerator[None]:
            yield
            tracing.shutdown()
            await singletons.dispose()

        application = FastAPI(title="Agente de atendimento ao aluno", lifespan=lifespan)
        application.add_middleware(
            CORSMiddleware,
            allow_origins=singletons.settings.cors_origins,
            allow_methods=CORS_METHODS,
            allow_headers=CORS_HEADERS,
            expose_headers=CORS_EXPOSED_HEADERS,
        )
        application.add_middleware(RequestLog)
        application.include_router(HealthRouter.build(HealthService(singletons.database)))
        StudentRoutes(singletons, tracing).mount(application)
        return application
