from http import HTTPStatus

from dishka.integrations.fastapi import DishkaRoute, FromDishka
from fastapi import APIRouter, HTTPException
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

router = APIRouter(route_class=DishkaRoute)


class ConfirmProposalRequest(BaseModel):
    token: str
    conversation_id: str
    message: str = ""
    confirmation_word: str = ""

    @property
    def answer(self) -> StudentAnswer:
        return StudentAnswer(self.message, self.confirmation_word)


@router.post("/protocols/proposals/confirm", status_code=HTTPStatus.CREATED)
async def confirm(
    request: ConfirmProposalRequest, service: FromDishka[ProtocolConfirmation]
) -> ConfirmedProtocolDto:
    try:
        return await service.confirm(request.token, request.conversation_id, request.answer)
    except ProposalNotFoundError, ConversationNotFoundError:
        raise _error(HTTPStatus.NOT_FOUND) from None
    except DuplicateProtocolError:
        raise _error(HTTPStatus.CONFLICT) from None
    except ServiceNotOpenableError as refused:
        unprocessable = HTTPStatus.UNPROCESSABLE_ENTITY
        raise HTTPException(unprocessable, refused.reason.value) from None


def _error(status: HTTPStatus) -> HTTPException:
    return HTTPException(status, status.phrase)
