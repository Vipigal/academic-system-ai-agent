import asyncio
from collections.abc import Awaitable, Callable

from langchain.agents.middleware import (
    AgentMiddleware,
    ModelCallResult,
    ModelRequest,
    ModelResponse,
)
from langchain.agents.middleware.types import AgentState

type PlainRequest = ModelRequest[None]
type PendingResponse = Awaitable[ModelResponse[None]]


class ProviderGate(AgentMiddleware[AgentState[None], None, None]):
    def __init__(self, semaphore: asyncio.Semaphore) -> None:
        super().__init__()
        self._semaphore = semaphore

    async def awrap_model_call(
        self, request: PlainRequest, handler: Callable[[PlainRequest], PendingResponse]
    ) -> ModelCallResult[None]:
        async with self._semaphore:
            return await handler(request)
