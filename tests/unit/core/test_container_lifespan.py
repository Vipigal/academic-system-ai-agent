from collections.abc import Iterator
from typing import cast

import pytest
from dishka import Provider, Scope, make_async_container, provide
from fastapi import FastAPI

from api.application.identity.service import IdentityService
from api.bootstrap.lifespan import ContainerLifespan
from api.domain.ports.protocol import ProposalSigner
from api.domain.ports.rate_limit import RateLimiter


class Warmup(Provider):
    scope = Scope.APP

    def __init__(self, failing: type | None) -> None:
        super().__init__()
        self.failing = failing
        self.finalized: list[type] = []

    @provide
    def identity(self) -> Iterator[IdentityService]:
        yield cast(IdentityService, object())
        self.finalized.append(IdentityService)

    @provide
    def signer(self) -> ProposalSigner:
        if self.failing is ProposalSigner:
            raise ValueError("falha no aquecimento")
        return cast(ProposalSigner, object())

    @provide
    def limiter(self) -> RateLimiter:
        return cast(RateLimiter, object())


async def test_the_container_closes_when_a_startup_check_raises() -> None:
    warmup = Warmup(failing=ProposalSigner)
    lifespan = ContainerLifespan(make_async_container(warmup))

    with pytest.raises(ValueError, match="aquecimento"):
        async with lifespan(FastAPI()):
            pytest.fail("o serve não deve começar")

    assert warmup.finalized == [IdentityService]


async def test_the_container_closes_when_serving_ends_with_an_exception() -> None:
    warmup = Warmup(failing=None)
    lifespan = ContainerLifespan(make_async_container(warmup))

    with pytest.raises(RuntimeError, match="serve"):
        async with lifespan(FastAPI()):
            raise RuntimeError("serve caiu")

    assert warmup.finalized == [IdentityService]
