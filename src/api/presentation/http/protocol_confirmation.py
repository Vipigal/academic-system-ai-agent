from collections.abc import Awaitable, Callable
from http import HTTPStatus
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from api.application.protocol.confirmation import ProtocolConfirmation
from api.application.protocol.dto.confirmation import ConfirmedProtocolDto
from api.domain.conversation.errors import ConversationNotFoundError
from api.domain.protocol.errors import (
    DuplicateProtocolError,
    ProposalNotFoundError,
    ServiceNotOpenableError,
)
from api.domain.protocol.opening import StudentAnswer


class ConfirmProposalRequest(BaseModel):
    token: str
    conversation_id: str
    message: str = ""
    confirmation_word: str = ""

    @property
    def answer(self) -> StudentAnswer:
        return StudentAnswer(self.message, self.confirmation_word)


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
                return await service.confirm(request.token, request.conversation_id, request.answer)
            except ProposalNotFoundError, ConversationNotFoundError:
                raise ProtocolConfirmationRouter._error(HTTPStatus.NOT_FOUND) from None
            except DuplicateProtocolError:
                raise ProtocolConfirmationRouter._error(HTTPStatus.CONFLICT) from None
            except ServiceNotOpenableError as refused:
                unprocessable = HTTPStatus.UNPROCESSABLE_ENTITY
                raise HTTPException(unprocessable, refused.reason.value) from None

        return router

    @staticmethod
    def _error(status: HTTPStatus) -> HTTPException:
        return HTTPException(status, status.phrase)
