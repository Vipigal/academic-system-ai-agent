import asyncio
from collections.abc import AsyncIterator
from typing import override

from langchain_core.messages import AIMessageChunk, BaseMessage
from langchain_core.outputs import ChatGenerationChunk
from pydantic import Field

from api.application.agent.scripted_model import ScriptedChatModel

CALL_SECONDS = 0.3


class SlowModel(ScriptedChatModel):
    active: list[int] = Field(default_factory=list)
    peaks: list[int] = Field(default_factory=list)

    @override
    async def _astream(
        self, messages: list[BaseMessage], *_: object, **__: object
    ) -> AsyncIterator[ChatGenerationChunk]:
        self.active.append(1)
        self.peaks.append(len(self.active))
        await asyncio.sleep(CALL_SECONDS)
        self.active.pop()
        yield ChatGenerationChunk(message=AIMessageChunk(content="resposta"))
