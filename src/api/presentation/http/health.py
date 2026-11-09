from http import HTTPStatus

from fastapi import APIRouter, Response

from api.application.health.dto.check import HealthDto
from api.application.health.service import HealthService


class HealthRouter:
    @staticmethod
    def build(service: HealthService) -> APIRouter:
        router = APIRouter()

        @router.get("/health/live")
        async def read_live() -> dict[str, str]:
            return {"status": "alive"}

        @router.get("/health/ready")
        async def read_ready(response: Response) -> HealthDto:
            health = await service.check()
            if not health.database_available:
                response.status_code = HTTPStatus.SERVICE_UNAVAILABLE
            return health

        return router
