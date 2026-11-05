from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from api.application.health_service import HealthService
from api.persistence.database import Database
from api.persistence.ownership_registry import OwnershipRegistry
from api.presentation.http.health import HealthRouter
from api.settings import Settings


class ApiFactory:
    @staticmethod
    def create(settings: Settings | None = None) -> FastAPI:
        OwnershipRegistry.assert_complete()
        resolved_settings = settings or Settings.from_environment()
        database = Database(resolved_settings.database_url.get_secret_value())

        @asynccontextmanager
        async def lifespan(_: FastAPI) -> AsyncGenerator[None]:
            yield
            await database.dispose()

        application = FastAPI(title="Agente de atendimento ao aluno", lifespan=lifespan)
        application.include_router(HealthRouter.build(HealthService(database)))
        return application
