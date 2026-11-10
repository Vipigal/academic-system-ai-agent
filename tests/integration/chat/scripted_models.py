import asyncio
from collections.abc import AsyncIterator
from typing import override

from langchain_core.messages import AIMessageChunk, BaseMessage
from langchain_core.outputs import ChatGenerationChunk
from pydantic import ConfigDict, Field

from tests.doubles.scripted_model import ScriptedChatModel

FIRST_WORD = "primeiro"
SECOND_WORD = "segundo"


class FailingModel(ScriptedChatModel):
    async def _astream(
        self, messages: list[BaseMessage], *_: object, **__: object
    ) -> AsyncIterator[ChatGenerationChunk]:
        yield ChatGenerationChunk(message=AIMessageChunk(content=""))
        raise ConnectionError(f"segredo-interno do provedor {len(messages)}")


class GatedModel(ScriptedChatModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    gate: asyncio.Event = Field(default_factory=asyncio.Event)

    @override
    async def _astream(
        self, messages: list[BaseMessage], *_: object, **__: object
    ) -> AsyncIterator[ChatGenerationChunk]:
        yield ChatGenerationChunk(message=AIMessageChunk(content=FIRST_WORD))
        await self.gate.wait()
        yield ChatGenerationChunk(message=AIMessageChunk(content=SECOND_WORD))
