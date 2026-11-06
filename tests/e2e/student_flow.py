import json
from dataclasses import dataclass
from http import HTTPStatus

import httpx

from tests.integration.chat.chat_client import (
    TOOL_INPUT,
    TOOL_OUTPUT,
    ChatClient,
    Chunk,
    chunks_of,
)

CONFIRM_ROUTE = "/protocols/proposals/confirm"
PROPOSE_TOOL = "propose_protocol"
LIST_TOOL = "list_protocols"


@dataclass(frozen=True, slots=True)
class FlowResult:
    proposal: list[Chunk]
    listing: list[Chunk]
    confirmation: httpx.Response

    @property
    def number(self) -> str:
        return str(self.confirmation.json()["protocol_number"])


def tools_called(chunks: list[Chunk]) -> list[object]:
    return [chunk["toolName"] for chunk in chunks if chunk["type"] == TOOL_INPUT]


def outputs_text(chunks: list[Chunk]) -> str:
    return json.dumps([chunk["output"] for chunk in chunks if chunk["type"] == TOOL_OUTPUT])


class StudentFlow:
    def __init__(self, client: httpx.AsyncClient, proposal_text: str, listing_text: str) -> None:
        self._client = client
        self._proposal_text = proposal_text
        self._listing_text = listing_text

    async def run(self) -> FlowResult:
        chat = await ChatClient.logged_in(self._client)
        conversation = await chat.create_conversation()
        asked = await chat.send(conversation, self._proposal_text)
        assert asked.status_code == HTTPStatus.OK
        proposal = chunks_of(asked.text)
        confirmation = await self._confirm(chat, proposal)
        return FlowResult(proposal, await self._list(chat, conversation), confirmation)

    async def _list(self, chat: ChatClient, conversation: str) -> list[Chunk]:
        listed = await chat.send(conversation, self._listing_text)
        assert listed.status_code == HTTPStatus.OK
        return chunks_of(listed.text)

    async def _confirm(self, chat: ChatClient, proposal: list[Chunk]) -> httpx.Response:
        token = _token_of(proposal)
        return await self._client.post(CONFIRM_ROUTE, json={"token": token}, headers=chat.headers)


def _token_of(chunks: list[Chunk]) -> str:
    proposed = next(
        chunk["toolCallId"]
        for chunk in chunks
        if chunk["type"] == TOOL_INPUT and chunk["toolName"] == PROPOSE_TOOL
    )
    output = next(
        chunk["output"]
        for chunk in chunks
        if chunk["type"] == TOOL_OUTPUT and chunk["toolCallId"] == proposed
    )
    assert isinstance(output, dict)
    return str(output["client_only"]["token"])
