from collections.abc import Iterator, Sequence

from langchain_core.messages import AIMessage, AnyMessage, HumanMessage, SystemMessage, ToolMessage
from langchain_core.messages.tool import tool_call

from api.application.agent.history import (
    PastAssistantMessage,
    PastMessage,
    PastSystemEvent,
    PastUserMessage,
)


class AgentMessages:
    @classmethod
    def of(cls, history: Sequence[PastMessage], message: str) -> list[AnyMessage]:
        past = [item for entry in history for item in cls._from_past(entry)]
        return [*past, HumanMessage(content=message)]

    @classmethod
    def _from_past(cls, entry: PastMessage) -> Iterator[AnyMessage]:
        if isinstance(entry, PastUserMessage):
            yield HumanMessage(content=entry.text)
            return
        if isinstance(entry, PastSystemEvent):
            yield SystemMessage(content=entry.text)
            return
        yield cls._assistant(entry)
        for call in entry.tool_calls:
            yield ToolMessage(
                content=call.seen_by_model, tool_call_id=call.tool_call_id, name=call.tool_name
            )

    @staticmethod
    def _assistant(entry: PastAssistantMessage) -> AIMessage:
        calls = [
            tool_call(name=call.tool_name, args=dict(call.arguments), id=call.tool_call_id)
            for call in entry.tool_calls
        ]
        return AIMessage(content=entry.text, tool_calls=calls)
