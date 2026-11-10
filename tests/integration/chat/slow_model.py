import asyncio
from collections.abc import AsyncIterator
from contextlib import suppress
from typing import override

from langchain_core.messages import AIMessageChunk, BaseMessage
from langchain_core.outputs import ChatGenerationChunk
from pydantic import Field, PrivateAttr

from tests.doubles.scripted_model import ScriptedChatModel

WAIT_SECONDS = 5.0


class SlowModel(ScriptedChatModel):
    expected: int
    active: list[int] = Field(default_factory=list)
    peaks: list[int] = Field(default_factory=list)
    _everyone_arrived: asyncio.Event = PrivateAttr(default_factory=asyncio.Event)

    @override
    async def _astream(
        self, messages: list[BaseMessage], *_: object, **__: object
    ) -> AsyncIterator[ChatGenerationChunk]:
        self.active.append(1)
        self.peaks.append(len(self.active))
        if len(self.active) >= self.expected:
            self._everyone_arrived.set()
        with suppress(TimeoutError):
            await asyncio.wait_for(self._everyone_arrived.wait(), WAIT_SECONDS)
        self.active.pop()
        yield ChatGenerationChunk(message=AIMessageChunk(content="resposta"))
