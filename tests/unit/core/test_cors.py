import secrets

import httpx

from api.bootstrap.app import ApiFactory
from api.bootstrap.containers import Containers
from api.bootstrap.settings import Settings

FRONT = "http://localhost:5173"
QUOTA_HEADERS = {"retry-after", "ratelimit-limit", "ratelimit-remaining", "ratelimit-reset"}


async def test_the_front_can_read_the_rate_limit_headers() -> None:
    settings = Settings.model_validate(
        {
            "database_url": "postgresql+asyncpg://nobody:nothing@127.0.0.1:1/nothing",
            "agent_model": "fake",
            "cors_origins": [FRONT],
            "jwt_secret": secrets.token_urlsafe(32),
            "proposal_secret": secrets.token_urlsafe(32),
        }
    )
    transport = httpx.ASGITransport(app=ApiFactory.assemble(settings, Containers.http(settings)))
    async with httpx.AsyncClient(transport=transport, base_url="http://api") as client:
        response = await client.get("/health/live", headers={"Origin": FRONT})

    exposed = response.headers["access-control-expose-headers"].lower().split(", ")
    assert set(exposed) == QUOTA_HEADERS
