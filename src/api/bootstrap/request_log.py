import logging
from time import perf_counter
from uuid import uuid4

from starlette.types import ASGIApp, Message, Receive, Scope, Send

from api.infrastructure.logging import LogContext

logger = logging.getLogger(__name__)
MILLISECONDS = 1000
QUIET_PATHS = frozenset({"/health/live", "/health/ready"})
UNFINISHED = 500


class RequestLog:
    def __init__(self, app: ASGIApp) -> None:
        self._app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http" or scope["path"] in QUIET_PATHS:
            await self._app(scope, receive, send)
            return
        LogContext.bind(uuid4().hex)
        status = [UNFINISHED]
        started = perf_counter()

        async def watching(message: Message) -> None:
            if message["type"] == "http.response.start":
                status[0] = message["status"]
            await send(message)

        try:
            await self._app(scope, receive, watching)
        finally:
            self._log(scope, status[0], started)

    @staticmethod
    def _log(scope: Scope, status: int, started: float) -> None:
        LogContext.bind_trace(LogContext.request_trace())
        elapsed = round((perf_counter() - started) * MILLISECONDS)
        logger.info("%s %s %s duration_ms=%s", scope["method"], scope["path"], status, elapsed)
