from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

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
        for checked in CHECKED_AT_STARTUP:
            await self._container.get(checked)
        yield
        await self._container.close()
