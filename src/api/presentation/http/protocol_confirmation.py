from collections.abc import Awaitable, Callable
from http import HTTPStatus
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from api.application.protocol.confirmation import ProtocolConfirmation
from api.application.protocol.dto.confirmation import ConfirmedProtocolDto
from api.domain.protocol.errors import (
    DuplicateProtocolError,
    ProposalNotFoundError,
    ServiceNotOpenableError,
)


class ConfirmProposalRequest(BaseModel):
    token: str


class ProtocolConfirmationRouter:
    @staticmethod
    def build(confirmation: Callable[..., Awaitable[ProtocolConfirmation]]) -> APIRouter:
        router = APIRouter()

        @router.post("/protocols/proposals/confirm", status_code=HTTPStatus.CREATED)
        async def confirm(
            request: ConfirmProposalRequest,
            service: Annotated[ProtocolConfirmation, Depends(confirmation)],
        ) -> ConfirmedProtocolDto:
            try:
                return await service.confirm(request.token)
            except ProposalNotFoundError:
                raise ProtocolConfirmationRouter._error(HTTPStatus.NOT_FOUND) from None
            except DuplicateProtocolError:
                raise ProtocolConfirmationRouter._error(HTTPStatus.CONFLICT) from None
            except ServiceNotOpenableError:
                raise ProtocolConfirmationRouter._error(HTTPStatus.UNPROCESSABLE_ENTITY) from None

        return router

    @staticmethod
    def _error(status: HTTPStatus) -> HTTPException:
        return HTTPException(status, status.phrase)
