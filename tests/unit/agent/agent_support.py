from collections.abc import Callable, Iterator, Mapping, Sequence

from langchain_core.messages import AIMessage, BaseMessage
from langchain_core.messages.tool import tool_call
from langchain_core.outputs import ChatGenerationChunk
from pydantic import Field

from api.application.agent.agent_runtime import AgentLimits, AgentRuntime
from api.application.agent.events import AgentEvent, ToolResultReceived
from api.application.agent.scripted_model import ScriptedChatModel
from api.application.agent.student_agent import StudentAgent
from api.application.agent.tools.registry import RegisteredTool, ToolRegistry
from api.infrastructure.clock import FixedClock
from tests.unit.agent.student_stubs import stub_student

FINAL_ANSWER = "Resposta final ao aluno."
DEFAULT_LIMITS = AgentLimits(model_calls=8, tool_calls=12, timeout_seconds=5)


class RecordingModel(ScriptedChatModel):
    seen: list[list[BaseMessage]] = Field(default_factory=list)

    def _next_of(self, messages: Sequence[BaseMessage]) -> AIMessage:
        self.seen.append(list(messages))
        return super()._next_of(messages)


class FlakyModel(ScriptedChatModel):
    failures_left: int = 1

    def _stream(
        self, messages: list[BaseMessage], *_: object, **__: object
    ) -> Iterator[ChatGenerationChunk]:
        if self.failures_left:
            self.failures_left -= 1
            raise ConnectionError("provedor fora")
        yield from super()._stream(messages)


def described[F: Callable[..., object]](description: str) -> Callable[[F], F]:
    def describe(function: F) -> F:
        function.__doc__ = description
        return function

    return describe


def call(
    name: str, arguments: Mapping[str, object] | None = None, call_id: str = "c1"
) -> AIMessage:
    request = tool_call(name=name, args=dict(arguments or {}), id=call_id)
    return AIMessage(content="", tool_calls=[request])


def answer(text: str = FINAL_ANSWER) -> AIMessage:
    return AIMessage(content=text)


def limits_with(
    model_calls: int = 8, tool_calls: int = 12, timeout_seconds: float = 5
) -> AgentLimits:
    return AgentLimits(model_calls, tool_calls, timeout_seconds)


def runtime_with(model: ScriptedChatModel, limits: AgentLimits = DEFAULT_LIMITS) -> AgentRuntime:
    return AgentRuntime.create(model, limits, FixedClock())


def agent_with(
    model: ScriptedChatModel,
    tools: Sequence[RegisteredTool] | None = None,
    limits: AgentLimits = DEFAULT_LIMITS,
) -> StudentAgent:
    registered = stub_student().registry().tools if tools is None else tools
    return StudentAgent(runtime_with(model, limits), registered, "trace-teste")


def tool_results(events: Sequence[AgentEvent]) -> list[ToolResultReceived]:
    return [event for event in events if isinstance(event, ToolResultReceived)]


def registered_of(group: object) -> tuple[RegisteredTool, ...]:
    return ToolRegistry(group).tools
