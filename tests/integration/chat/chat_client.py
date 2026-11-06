import json
from collections.abc import Sequence
from dataclasses import dataclass
from http import HTTPStatus
from uuid import UUID

import httpx

from api.domain.conversation.message import Message
from api.persistence.agent.repository import SqlConversationRepository
from api.persistence.core.database import Database
from api.persistence.core.repository_adapter import RepositoryAdapter
from api.persistence.identity.student_session_repository import StudentSessionRepository

STUDENT = "UniSaoPaulo:180017"
STUDENT_PERSON = "3000003"
OTHER_STUDENT = "UniMontanhas:070017"
WINDOW = 20
TEXT_DELTA = "text-delta"
TOOL_INPUT = "tool-input-available"
TOOL_OUTPUT = "tool-output-available"
DONE_FRAME = "data: [DONE]"

type Chunk = dict[str, object]


def user_message(text: str) -> dict[str, object]:
    return {"id": "m1", "role": "user", "parts": [{"type": "text", "text": text}]}


def assistant_message(text: str) -> dict[str, object]:
    return {"id": "m0", "role": "assistant", "parts": [{"type": "text", "text": text}]}


def chunks_of(text: str) -> list[Chunk]:
    frames = [frame for frame in text.split("\n\n") if frame]
    assert frames[-1] == DONE_FRAME
    return [json.loads(frame.removeprefix("data: ")) for frame in frames[:-1]]


def kinds_of(chunks: Sequence[Chunk]) -> list[object]:
    return [chunk["type"] for chunk in chunks]


def first_of(chunks: Sequence[Chunk], kind: str) -> Chunk:
    return next(chunk for chunk in chunks if chunk["type"] == kind)


def transmitted_text(chunks: Sequence[Chunk]) -> str:
    return "".join(str(chunk["delta"]) for chunk in chunks if chunk["type"] == TEXT_DELTA)


@dataclass(frozen=True, slots=True)
class Exchange:
    conversation: str
    response: httpx.Response

    @property
    def chunks(self) -> list[Chunk]:
        return chunks_of(self.response.text)


def client_token_of(done: Exchange) -> str:
    output = first_of(done.chunks, TOOL_OUTPUT)["output"]
    assert isinstance(output, dict)
    return str(output["client_only"]["token"])


class ChatClient:
    def __init__(self, client: httpx.AsyncClient, token: str = "") -> None:
        self._client = client
        self.token = token

    @classmethod
    async def logged_in(cls, client: httpx.AsyncClient, student: str = STUDENT) -> ChatClient:
        response = await client.post("/auth/dev-login", json={"student": student})
        assert response.status_code == HTTPStatus.OK
        return cls(client, str(response.json()["access_token"]))

    @property
    def headers(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self.token}"} if self.token else {}

    async def create_conversation(self) -> str:
        response = await self._client.post("/conversations", headers=self.headers)
        assert response.status_code == HTTPStatus.CREATED
        return str(response.json()["id"])

    async def post(self, conversation: str, messages: Sequence[object]) -> httpx.Response:
        body = {"id": conversation, "messages": messages, "trigger": "submit-message"}
        return await self._client.post("/chat", json=body, headers=self.headers)

    async def send(self, conversation: str, text: str) -> httpx.Response:
        return await self.post(conversation, [user_message(text)])

    async def exchange(self, *messages: object) -> Exchange:
        conversation = await self.create_conversation()
        return Exchange(conversation, await self.post(conversation, messages))


async def history_of(database: Database, conversation: str) -> Sequence[Message]:
    factory = database.db_session_factory
    session = await StudentSessionRepository(factory).load(STUDENT_PERSON)
    repository = SqlConversationRepository(RepositoryAdapter(factory, session))
    return await repository.window(UUID(conversation), WINDOW)
