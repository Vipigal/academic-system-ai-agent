import secrets
from http import HTTPStatus

import httpx
import pytest
from fastapi import FastAPI

from api.bootstrap.app import ApiFactory
from api.bootstrap.settings import Settings

PROTECTED = [
    ("/chat", "post"),
    ("/conversations", "post"),
    ("/protocols/proposals/confirm", "post"),
]
OPEN = [("/auth/dev-login", "post"), ("/auth/dev-students", "get"), ("/health/live", "get")]


def application() -> FastAPI:
    settings = Settings.model_validate(
        {
            "database_url": "postgresql+asyncpg://nobody:nothing@127.0.0.1:1/nothing",
            "agent_model": "fake",
            "dev_login": True,
            "jwt_secret": secrets.token_urlsafe(32),
            "proposal_secret": secrets.token_urlsafe(32),
        }
    )
    return ApiFactory.create(settings)


@pytest.mark.parametrize("path", ["/chat", "/protocols/proposals/confirm"])
async def test_without_a_token_an_invalid_body_is_unauthorized_not_unprocessable(
    path: str,
) -> None:
    transport = httpx.ASGITransport(app=application())
    async with httpx.AsyncClient(transport=transport, base_url="http://api") as client:
        response = await client.post(path, json={"invalido": True})

    assert response.status_code == HTTPStatus.UNAUTHORIZED
    assert response.headers["www-authenticate"] == "Bearer"
    assert response.json() == {"detail": HTTPStatus.UNAUTHORIZED.phrase}


def secured_routes() -> dict[tuple[str, str], bool]:
    paths = application().openapi()["paths"]
    return {
        (path, method): bool(operation.get("security"))
        for path, methods in paths.items()
        for method, operation in methods.items()
    }


def test_the_openapi_declares_the_bearer_scheme_on_the_authenticated_routes_only() -> None:
    schemes = application().openapi()["components"]["securitySchemes"]
    secured = secured_routes()

    assert schemes["HTTPBearer"] == {"type": "http", "scheme": "bearer"}
    assert all(secured[route] for route in PROTECTED)
    assert not any(secured[route] for route in OPEN)
