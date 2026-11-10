from http import HTTPStatus

import httpx
from fastapi import FastAPI
from pydantic import SecretStr

from api.bootstrap.app import ApiFactory
from api.bootstrap.containers import Containers
from api.bootstrap.settings import Settings
from tests.integration.chat.chat_settings import settings_with

UNREACHABLE_DATABASE = "postgresql+asyncpg://nobody:nothing@127.0.0.1:1/nothing"


def assembled(settings: Settings) -> FastAPI:
    return ApiFactory.assemble(settings, Containers.http(settings))


async def get_path(application: FastAPI, path: str) -> httpx.Response:
    transport = httpx.ASGITransport(app=application)
    async with httpx.AsyncClient(transport=transport, base_url="http://api") as client:
        return await client.get(path)


async def test_live_answers_without_the_database() -> None:
    settings = settings_with(database_url=SecretStr(UNREACHABLE_DATABASE))
    response = await get_path(assembled(settings), "/health/live")
    assert response.status_code == HTTPStatus.OK


async def test_ready_reports_healthy_when_the_database_answers() -> None:
    response = await get_path(assembled(settings_with()), "/health/ready")
    assert response.status_code == HTTPStatus.OK
    assert response.json() == {"database_available": True}


async def test_ready_reports_unavailable_when_the_database_does_not_answer() -> None:
    settings = settings_with(database_url=SecretStr(UNREACHABLE_DATABASE))
    response = await get_path(assembled(settings), "/health/ready")
    assert response.status_code == HTTPStatus.SERVICE_UNAVAILABLE
    assert response.json() == {"database_available": False}


async def test_the_old_health_path_is_gone() -> None:
    response = await get_path(assembled(settings_with()), "/health")
    assert response.status_code == HTTPStatus.NOT_FOUND
