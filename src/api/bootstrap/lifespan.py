from collections.abc import AsyncGenerator
from contextlib import AsyncExitStack, asynccontextmanager

from dishka import AsyncContainer
from fastapi import FastAPI

from api.application.identity.service import IdentityService
from api.domain.ports.protocol import ProposalSigner
from api.domain.ports.rate_limit import RateLimiter

CHECKED_AT_STARTUP = (IdentityService, ProposalSigner, RateLimiter)


class ContainerLifespan:
    def __init__(self, container: AsyncContainer) -> None:
        self._container = container

    @asynccontextmanager
    async def __call__(self, _: FastAPI) -> AsyncGenerator[None]:
        async with AsyncExitStack() as stack:
            stack.push_async_callback(self._container.close)
            await self._warm_up()
            yield

    async def _warm_up(self) -> None:
        for checked in CHECKED_AT_STARTUP:
            await self._container.get(checked)
