from collections.abc import Mapping, Sequence
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class PastToolCall:
    tool_call_id: str
    tool_name: str
    arguments: Mapping[str, object]
    seen_by_model: str


@dataclass(frozen=True, slots=True)
class PastUserMessage:
    text: str


@dataclass(frozen=True, slots=True)
class PastAssistantMessage:
    text: str
    tool_calls: Sequence[PastToolCall] = ()


@dataclass(frozen=True, slots=True)
class PastSystemEvent:
    text: str


type PastMessage = PastUserMessage | PastAssistantMessage | PastSystemEvent
