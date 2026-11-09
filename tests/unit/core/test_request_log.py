import json
import logging

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from api.bootstrap.request_log import RequestLog
from api.infrastructure.logging import JsonFormatter, LogContext


def application() -> FastAPI:
    app = FastAPI()
    app.add_middleware(RequestLog)

    @app.get("/ping")
    async def ping() -> dict[str, str]:
        LogContext.bind_trace("trace-from-the-endpoint")
        return {}

    @app.get("/health/live")
    async def live() -> dict[str, str]:
        return {}

    @app.get("/health/ready")
    async def ready() -> dict[str, str]:
        return {}

    return app


async def get(path: str) -> None:
    transport = ASGITransport(app=application())
    async with AsyncClient(transport=transport, base_url="http://api") as client:
        await client.get(path, params={"cpf": "12345678909"})


async def test_each_request_logs_one_json_line_without_query_or_body(
    caplog: pytest.LogCaptureFixture,
) -> None:
    with caplog.at_level(logging.INFO, logger="api.bootstrap.request_log"):
        await get("/ping")

    entry = json.loads(JsonFormatter().format(caplog.records[0]))
    assert len(caplog.records) == 1
    assert entry["message"].startswith("GET /ping 200 duration_ms=")
    assert "12345678909" not in caplog.text
    assert entry["request_id"]
    assert entry["trace_id"] == "trace-from-the-endpoint"


@pytest.mark.parametrize("path", ["/health/live", "/health/ready"])
async def test_the_health_probes_are_not_logged(
    path: str, caplog: pytest.LogCaptureFixture
) -> None:
    with caplog.at_level(logging.INFO, logger="api.bootstrap.request_log"):
        await get(path)

    assert not caplog.records
