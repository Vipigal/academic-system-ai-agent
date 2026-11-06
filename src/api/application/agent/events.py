from collections.abc import Mapping
from dataclasses import dataclass
from enum import StrEnum


class StopReason(StrEnum):
    COMPLETED = "completed"
    MODEL_CALL_LIMIT = "model_call_limit"


@dataclass(frozen=True, slots=True)
class TokenUsage:
    tokens_in: int = 0
    tokens_out: int = 0


@dataclass(frozen=True, slots=True)
class TextDelta:
    text: str


@dataclass(frozen=True, slots=True)
class ToolCallRequested:
    tool_call_id: str
    tool_name: str
    arguments: Mapping[str, object]


@dataclass(frozen=True, slots=True)
class ToolResultReceived:
    tool_call_id: str
    tool_name: str
    status: str
    seen_by_model: str
    complete: Mapping[str, object]
    duration_ms: int


@dataclass(frozen=True, slots=True)
class AgentFinished:
    text: str
    stop_reason: StopReason
    usage: TokenUsage


type AgentEvent = TextDelta | ToolCallRequested | ToolResultReceived | AgentFinished


@dataclass(frozen=True, slots=True)
class AgentRun:
    text: str
    stop_reason: StopReason
    usage: TokenUsage
    events: tuple[AgentEvent, ...]
