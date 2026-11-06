from http import HTTPStatus

import httpx
from fastapi import FastAPI
from pydantic import SecretStr

from api.bootstrap.app import ApiFactory
from api.bootstrap.settings import Settings

UNREACHABLE_DATABASE = "postgresql+asyncpg://nobody:nothing@127.0.0.1:1/nothing"


async def get_health(application: FastAPI) -> httpx.Response:
    transport = httpx.ASGITransport(app=application)
    async with httpx.AsyncClient(transport=transport, base_url="http://api") as client:
        return await client.get("/health")


async def test_reports_healthy_when_the_database_answers() -> None:
    response = await get_health(ApiFactory.create())
    assert response.status_code == HTTPStatus.OK
    assert response.json() == {"database_available": True}


async def test_reports_unavailable_when_the_database_does_not_answer() -> None:
    settings = Settings(database_url=SecretStr(UNREACHABLE_DATABASE))
    response = await get_health(ApiFactory.create(settings))
    assert response.status_code == HTTPStatus.SERVICE_UNAVAILABLE
    assert response.json() == {"database_available": False}
