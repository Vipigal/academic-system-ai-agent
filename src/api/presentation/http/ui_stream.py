import json
from collections.abc import AsyncGenerator, Iterator
from contextlib import aclosing
from uuid import uuid4

from api.application.agent.events import TextDelta, ToolCallRequested, ToolResultReceived
from api.application.chat.events import ChatEvent, TurnFailed

type Chunk = dict[str, object]

HEADERS = {
    "content-type": "text/event-stream",
    "cache-control": "no-cache",
    "connection": "keep-alive",
    "x-vercel-ai-ui-message-stream": "v1",
    "x-accel-buffering": "no",
}
END_OF_STREAM = "data: [DONE]\n\n"
GENERIC_ERROR = "Não consegui responder agora. Tente de novo em instantes."
START_STEP = "start-step"
FINISH_STEP = "finish-step"


def _chunk(kind: str, **fields: object) -> Chunk:
    return {"type": kind, **fields}


class UiMessageStream:
    @classmethod
    async def of(cls, events: AsyncGenerator[ChatEvent]) -> AsyncGenerator[str]:
        chunks = UiChunks()
        yield cls._frame(_chunk("start", messageId=uuid4().hex))
        yield cls._frame(_chunk(START_STEP))
        async with aclosing(events):
            async for event in events:
                for chunk in chunks.of(event):
                    yield cls._frame(chunk)
        yield END_OF_STREAM

    @staticmethod
    def _frame(chunk: Chunk) -> str:
        return f"data: {json.dumps(chunk, ensure_ascii=False, separators=(',', ':'))}\n\n"


class UiChunks:
    def __init__(self) -> None:
        self._text_id: str | None = None
        self._step_has_output = False

    def of(self, event: ChatEvent) -> Iterator[Chunk]:
        if isinstance(event, TextDelta):
            yield from self._text(event)
        elif isinstance(event, ToolCallRequested):
            yield from self._tool_input(event)
        elif isinstance(event, ToolResultReceived):
            self._step_has_output = True
            yield _chunk(
                "tool-output-available", toolCallId=event.tool_call_id, output=dict(event.complete)
            )
        else:
            yield from self._closing(event)

    def _text(self, event: TextDelta) -> Iterator[Chunk]:
        yield from self._next_step()
        if self._text_id is None:
            self._text_id = uuid4().hex
            yield _chunk("text-start", id=self._text_id)
        yield _chunk("text-delta", id=self._text_id, delta=event.text)

    def _tool_input(self, event: ToolCallRequested) -> Iterator[Chunk]:
        yield from self._next_step()
        yield from self._end_text()
        yield _chunk(
            "tool-input-available",
            toolCallId=event.tool_call_id,
            toolName=event.tool_name,
            input=dict(event.arguments),
        )

    def _closing(self, event: ChatEvent) -> Iterator[Chunk]:
        yield from self._end_text()
        if isinstance(event, TurnFailed):
            yield _chunk("error", errorText=GENERIC_ERROR)
        yield _chunk(FINISH_STEP)
        yield _chunk("finish")

    def _next_step(self) -> Iterator[Chunk]:
        if self._step_has_output:
            self._step_has_output = False
            yield _chunk(FINISH_STEP)
            yield _chunk(START_STEP)

    def _end_text(self) -> Iterator[Chunk]:
        if self._text_id is not None:
            yield _chunk("text-end", id=self._text_id)
            self._text_id = None
