from time import perf_counter

from api.application.agent.events import (
    AgentEvent,
    TextDelta,
    TokenUsage,
    ToolCallRequested,
    ToolResultReceived,
)
from api.application.chat.past_messages import SeenByModel
from api.domain.conversation.message import Message, MessageRole, ToolCall

MILLISECONDS = 1000


class TurnRecord:
    def __init__(self, question: str, model: str) -> None:
        self._question = question
        self._model = model
        self._started = perf_counter()
        self._transmitted: list[str] = []
        self._requests: dict[str, ToolCallRequested] = {}
        self._calls: list[ToolCall] = []

    def add(self, event: AgentEvent) -> None:
        if isinstance(event, TextDelta):
            self._transmitted.append(event.text)
        elif isinstance(event, ToolCallRequested):
            self._requests[event.tool_call_id] = event
        elif isinstance(event, ToolResultReceived):
            self._calls.append(self._call_of(event))

    def messages(self, usage: TokenUsage) -> tuple[Message, Message]:
        elapsed = (perf_counter() - self._started) * MILLISECONDS
        reply = Message(
            role=MessageRole.ASSISTANT,
            content="".join(self._transmitted),
            tool_calls=tuple(self._calls),
            model=self._model,
            tokens_in=usage.tokens_in,
            tokens_out=usage.tokens_out,
            latency_ms=round(elapsed),
        )
        return Message(MessageRole.USER, self._question), reply

    def _call_of(self, event: ToolResultReceived) -> ToolCall:
        request = self._requests.get(event.tool_call_id)
        return ToolCall(
            id=event.tool_call_id,
            name=event.tool_name,
            arguments=dict(request.arguments) if request else {},
            result=SeenByModel.to_result(event.seen_by_model),
            status=event.status,
            duration_ms=event.duration_ms,
        )
