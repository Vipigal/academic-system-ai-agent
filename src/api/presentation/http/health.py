from http import HTTPStatus

from dishka.integrations.fastapi import DishkaRoute, FromDishka
from fastapi import APIRouter, Response

from api.application.health.dto.check import HealthDto
from api.application.health.service import HealthService

router = APIRouter(route_class=DishkaRoute)


@router.get("/health/live")
async def read_live() -> dict[str, str]:
    return {"status": "alive"}


@router.get("/health/ready")
async def read_ready(response: Response, service: FromDishka[HealthService]) -> HealthDto:
    health = await service.check()
    if not health.database_available:
        response.status_code = HTTPStatus.SERVICE_UNAVAILABLE
    return health
