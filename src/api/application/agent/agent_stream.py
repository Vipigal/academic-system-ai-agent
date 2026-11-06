from collections.abc import Iterator, Mapping, Sequence

from langchain_core.messages import AIMessage, ToolMessage
from langgraph.types import StreamMode

from api.application.agent.events import (
    AgentEvent,
    AgentFinished,
    StopReason,
    TextDelta,
    TokenUsage,
    ToolCallRequested,
    ToolResultReceived,
)
from api.application.agent.langchain_tools import ToolExecution
from api.application.shared.tool_result import ToolResult, ToolStatus

MESSAGES_KEY = "messages"
NO_ANSWER_TEXT = (
    "Não consegui concluir sua resposta desta vez. Pode reformular a pergunta ou tentar de novo?"
)
STREAM_MODES: Sequence[StreamMode] = ("messages", "updates")


class StreamTranslator:
    def __init__(self) -> None:
        self._final_text = ""
        self._tokens_in = 0
        self._tokens_out = 0

    def translate(self, mode: str, payload: object) -> Iterator[AgentEvent]:
        if mode == MESSAGES_KEY:
            yield from self._from_token(payload)
        elif isinstance(payload, Mapping):
            for update in payload.values():
                yield from self._from_update(update)

    def closing(self, stop_reason: StopReason) -> Iterator[AgentEvent]:
        text = self._final_text
        if not text:
            text = NO_ANSWER_TEXT
            yield TextDelta(text)
        yield AgentFinished(text, stop_reason, TokenUsage(self._tokens_in, self._tokens_out))

    @staticmethod
    def _from_token(payload: object) -> Iterator[TextDelta]:
        token = payload[0] if isinstance(payload, tuple) else None
        if isinstance(token, AIMessage) and token.text:
            yield TextDelta(token.text)

    def _from_update(self, update: object) -> Iterator[AgentEvent]:
        messages = update.get(MESSAGES_KEY, ()) if isinstance(update, Mapping) else ()
        for message in messages:
            if isinstance(message, AIMessage):
                yield from self._from_model(message)
            elif isinstance(message, ToolMessage):
                yield ToolResultEvents.of(message)

    def _from_model(self, message: AIMessage) -> Iterator[ToolCallRequested]:
        usage = message.usage_metadata
        if usage:
            self._tokens_in += usage["input_tokens"]
            self._tokens_out += usage["output_tokens"]
        if not message.tool_calls:
            self._final_text = message.text
        for call in message.tool_calls:
            call_id = call["id"] or ""
            yield ToolCallRequested(call_id, call["name"], call["args"])


class ToolResultEvents:
    @classmethod
    def of(cls, message: ToolMessage) -> ToolResultReceived:
        execution = cls._execution_of(message)
        return ToolResultReceived(
            tool_call_id=message.tool_call_id,
            tool_name=message.name or "",
            status=execution.result.status.value,
            seen_by_model=message.text,
            complete=cls._complete(execution.result),
            duration_ms=execution.duration_ms,
        )

    @staticmethod
    def _execution_of(message: ToolMessage) -> ToolExecution:
        if isinstance(message.artifact, ToolExecution):
            return message.artifact
        result = ToolResult[object](status=ToolStatus.INVALID, explanation=message.text)
        return ToolExecution(result, duration_ms=0)

    @staticmethod
    def _complete(result: ToolResult[object]) -> Mapping[str, object]:
        dumped: dict[str, object] = result.model_dump(mode="json")
        if result.client_only is None:
            return dumped
        return {**dumped, "client_only": dict(result.client_only)}
