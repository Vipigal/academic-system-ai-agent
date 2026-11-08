import json
from collections.abc import Iterator, Mapping, Sequence

from api.application.agent.history import (
    PastAssistantMessage,
    PastMessage,
    PastSystemEvent,
    PastToolCall,
    PastUserMessage,
)
from api.domain.conversation.message import Message, MessageRole, ToolCall

PLAIN_TEXT = "text"


class SeenByModel:
    @staticmethod
    def to_result(seen: str) -> dict[str, object]:
        try:
            parsed = json.loads(seen)
        except json.JSONDecodeError:
            return {PLAIN_TEXT: seen}
        return parsed if isinstance(parsed, dict) else {PLAIN_TEXT: seen}

    @staticmethod
    def to_text(result: Mapping[str, object] | None) -> str:
        if result is None:
            return ""
        if result.keys() == {PLAIN_TEXT}:
            return str(result[PLAIN_TEXT])
        return json.dumps(result, ensure_ascii=False, separators=(",", ":"))


class PastMessages:
    @classmethod
    def of(cls, window: Sequence[Message]) -> list[PastMessage]:
        return [past for message in window for past in cls._from_message(message)]

    @classmethod
    def _from_message(cls, message: Message) -> Iterator[PastMessage]:
        if message.role is MessageRole.USER:
            yield PastUserMessage(message.content)
            return
        if message.role is MessageRole.SYSTEM_EVENT:
            yield PastSystemEvent(message.content)
            return
        if message.tool_calls:
            calls = tuple(cls._past_call(call) for call in message.tool_calls)
            yield PastAssistantMessage("", calls)
        yield PastAssistantMessage(message.content)

    @staticmethod
    def _past_call(call: ToolCall) -> PastToolCall:
        return PastToolCall(call.id, call.name, call.arguments, SeenByModel.to_text(call.result))
