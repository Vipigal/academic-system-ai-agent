from http import HTTPStatus

from fastapi import APIRouter, Response

from api.application.dto.health_dto import HealthDto
from api.application.health_service import HealthService


class HealthRouter:
    @staticmethod
    def build(service: HealthService) -> APIRouter:
        router = APIRouter()

        @router.get("/health")
        async def read_health(response: Response) -> HealthDto:
            health = await service.check()
            if not health.database_available:
                response.status_code = HTTPStatus.SERVICE_UNAVAILABLE
            return health

        return router
