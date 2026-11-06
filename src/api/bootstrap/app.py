from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from api.application.health.service import HealthService
from api.bootstrap.settings import Settings
from api.bootstrap.singletons import Singletons
from api.persistence.core.ownership_registry import OwnershipRegistry
from api.presentation.http.health import HealthRouter


class ApiFactory:
    @staticmethod
    def create(settings: Settings | None = None) -> FastAPI:
        OwnershipRegistry.assert_complete()
        singletons = Singletons.create(settings or Settings.from_environment())

        @asynccontextmanager
        async def lifespan(_: FastAPI) -> AsyncGenerator[None]:
            yield
            await singletons.dispose()

        application = FastAPI(title="Agente de atendimento ao aluno", lifespan=lifespan)
        application.include_router(HealthRouter.build(HealthService(singletons.database)))
        return application
