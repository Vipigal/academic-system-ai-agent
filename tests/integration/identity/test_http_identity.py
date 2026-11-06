import secrets
from http import HTTPStatus
from typing import Annotated

import httpx
import jwt
import pytest
from fastapi import Depends, FastAPI
from pydantic import BaseModel, SecretStr

from api.bootstrap.identity_providers import IdentityProviders
from api.bootstrap.settings import Settings
from api.domain.identity.session import StudentSession
from api.persistence.core.database import Database

SECRET = secrets.token_urlsafe(32)
FIRST_STUDENT = "UniSaoPaulo:180017"
SECOND_STUDENT = "UniMontanhas:070017"


class WhoAmIRequest(BaseModel):
    person_id: str


def settings_with(**overrides: object) -> Settings:
    base = Settings.from_environment()
    return base.model_copy(update={"jwt_secret": SecretStr(SECRET), "dev_login": True, **overrides})


def build_app(database: Database, settings: Settings) -> FastAPI:
    providers = IdentityProviders(settings, database)
    application = FastAPI()
    router = providers.auth_router()
    if router is not None:
        application.include_router(router)
    session_dependency = providers.session_dependency()

    @application.post("/whoami")
    async def whoami(
        request: WhoAmIRequest,
        session: Annotated[StudentSession, Depends(session_dependency)],
    ) -> dict[str, list[str]]:
        return {"person_ids": sorted(session.person_ids), "claimed": [request.person_id]}

    return application


def client_of(application: FastAPI) -> httpx.AsyncClient:
    return httpx.AsyncClient(transport=httpx.ASGITransport(app=application), base_url="http://api")


@pytest.fixture
def client(database: Database) -> httpx.AsyncClient:
    return client_of(build_app(database, settings_with()))


async def login(client: httpx.AsyncClient, student: str) -> str:
    response = await client.post("/auth/dev-login", json={"student": student})
    assert response.status_code == HTTPStatus.OK
    return str(response.json()["access_token"])


async def whoami(
    client: httpx.AsyncClient, token: str | None, body_id: str = "x"
) -> httpx.Response:
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    return await client.post("/whoami", json={"person_id": body_id}, headers=headers)


async def test_login_returns_a_token_whose_session_is_the_student(
    client: httpx.AsyncClient,
) -> None:
    async with client:
        token = await login(client, FIRST_STUDENT)
        response = await whoami(client, token)
    assert response.status_code == HTTPStatus.OK
    assert "3000003" in response.json()["person_ids"]


async def test_two_students_get_different_sessions_from_the_same_flow(
    client: httpx.AsyncClient,
) -> None:
    async with client:
        first = await whoami(client, await login(client, FIRST_STUDENT))
        second = await whoami(client, await login(client, SECOND_STUDENT))
    assert first.json()["person_ids"] != second.json()["person_ids"]
    assert not set(first.json()["person_ids"]) & set(second.json()["person_ids"])


async def test_the_body_id_never_changes_the_session(client: httpx.AsyncClient) -> None:
    async with client:
        token = await login(client, FIRST_STUDENT)
        honest = await whoami(client, token)
        forged = await whoami(client, token, body_id="3001982")
    assert forged.json()["person_ids"] == honest.json()["person_ids"]
    assert forged.json()["claimed"] == ["3001982"]


async def test_unknown_student_is_not_found(client: httpx.AsyncClient) -> None:
    async with client:
        responses = [
            await client.post("/auth/dev-login", json={"student": student})
            for student in ("UniSaoPaulo:000000", "malformed", "UniSaoPaulo:", ":180017")
        ]
    assert {response.status_code for response in responses} == {HTTPStatus.NOT_FOUND}
    assert len({response.text for response in responses}) == 1


async def test_protected_route_without_token_is_unauthorized(client: httpx.AsyncClient) -> None:
    async with client:
        response = await whoami(client, None)
    assert response.status_code == HTTPStatus.UNAUTHORIZED


async def test_tampered_token_is_unauthorized(client: httpx.AsyncClient) -> None:
    async with client:
        token = await login(client, FIRST_STUDENT)
        response = await whoami(client, token[:-2] + ("AA" if token[-2:] != "AA" else "BB"))
    assert response.status_code == HTTPStatus.UNAUTHORIZED


async def test_expired_token_is_unauthorized(database: Database) -> None:
    async with client_of(build_app(database, settings_with(jwt_ttl_minutes=-1))) as client:
        response = await whoami(client, await login(client, FIRST_STUDENT))
    assert response.status_code == HTTPStatus.UNAUTHORIZED


async def test_token_for_an_unknown_person_is_unauthorized(client: httpx.AsyncClient) -> None:
    forged = jwt.encode({"sub": "nobody", "exp": 4102444800}, SECRET, algorithm="HS256")
    async with client:
        response = await whoami(client, forged)
    assert response.status_code == HTTPStatus.UNAUTHORIZED


async def test_unauthorized_responses_carry_no_detail(client: httpx.AsyncClient) -> None:
    async with client:
        missing = await whoami(client, None)
        garbage = await whoami(client, "garbage")
    assert missing.text == garbage.text


async def test_login_route_does_not_exist_with_dev_login_off(database: Database) -> None:
    async with client_of(build_app(database, settings_with(dev_login=False))) as client:
        response = await client.post("/auth/dev-login", json={"student": FIRST_STUDENT})
    assert response.status_code == HTTPStatus.NOT_FOUND


def test_a_missing_secret_fails_closed(database: Database) -> None:
    with pytest.raises(ValueError, match="secret"):
        IdentityProviders(settings_with(jwt_secret=None), database)
