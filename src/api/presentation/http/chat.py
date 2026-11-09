from collections.abc import Awaitable, Callable
from http import HTTPStatus
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field, model_validator

from api.application.chat.dto.conversation import ConversationDto
from api.application.chat.service import ChatService
from api.domain.conversation.errors import ConversationNotFoundError
from api.presentation.http.ui_stream import HEADERS, UiMessageStream

USER_ROLE = "user"
TEXT_PART = "text"
MAX_PART_TEXT = 4000
MAX_MESSAGES = 200


class UiMessagePart(BaseModel):
    type: str
    text: str = Field(default="", max_length=MAX_PART_TEXT)


class UiMessage(BaseModel):
    role: str
    parts: list[UiMessagePart] = Field(default_factory=list)

    @property
    def text(self) -> str:
        return "".join(part.text for part in self.parts if part.type == TEXT_PART)


class ChatRequest(BaseModel):
    id: str
    messages: list[UiMessage] = Field(max_length=MAX_MESSAGES)

    @property
    def last_user_text(self) -> str:
        users = [message for message in self.messages if message.role == USER_ROLE]
        return users[-1].text if users else ""

    @model_validator(mode="after")
    def require_user_text(self) -> ChatRequest:
        if not self.last_user_text.strip():
            raise ValueError("o corpo precisa de uma mensagem do aluno com texto")
        return self


class ChatRouter:
    @staticmethod
    def build(chat_service: Callable[..., Awaitable[ChatService]]) -> APIRouter:
        router = APIRouter()

        @router.post("/conversations", status_code=HTTPStatus.CREATED)
        async def create_conversation(
            service: Annotated[ChatService, Depends(chat_service)],
        ) -> ConversationDto:
            return await service.create_conversation()

        @router.post("/chat")
        async def chat(
            request: ChatRequest,
            service: Annotated[ChatService, Depends(chat_service)],
        ) -> StreamingResponse:
            try:
                events = await service.begin(request.id, request.last_user_text)
            except ConversationNotFoundError:
                raise HTTPException(HTTPStatus.NOT_FOUND, HTTPStatus.NOT_FOUND.phrase) from None
            return StreamingResponse(UiMessageStream.of(events), headers=HEADERS)

        return router
