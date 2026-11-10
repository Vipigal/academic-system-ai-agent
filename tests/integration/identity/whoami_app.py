from dishka.integrations.fastapi import DishkaRoute, FromDishka, setup_dishka
from fastapi import APIRouter, FastAPI
from pydantic import BaseModel

from api.bootstrap.routes import ApiRoutes
from api.bootstrap.settings import Settings
from api.domain.identity.session import StudentSession
from api.persistence.core.database import Database
from tests.doubles.doubles import DoubleContainers


class WhoAmIRequest(BaseModel):
    person_id: str


def build_app(database: Database, settings: Settings) -> FastAPI:
    application = FastAPI()
    ApiRoutes.mount(application, settings)
    router = APIRouter(route_class=DishkaRoute)

    @router.post("/whoami")
    async def whoami(
        request: WhoAmIRequest,
        session: FromDishka[StudentSession],
    ) -> dict[str, list[str]]:
        return {"person_ids": sorted(session.person_ids), "claimed": [request.person_id]}

    application.include_router(router)
    setup_dishka(DoubleContainers.http(settings, {Database: database}), application)
    return application
