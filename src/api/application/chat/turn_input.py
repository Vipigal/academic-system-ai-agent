from collections.abc import Callable, Sequence
from contextlib import AbstractContextManager
from dataclasses import dataclass
from uuid import UUID

from api.application.agent.history import PastMessage
from api.application.agent.student_agent import StudentAgent

type AgentScope = Callable[[UUID], AbstractContextManager[StudentAgent]]


@dataclass(frozen=True, slots=True)
class ChatOptions:
    person_id: str
    history_window: int
    model: str


@dataclass(frozen=True, slots=True)
class TurnInput:
    conversation: UUID
    message: str
    past: Sequence[PastMessage]
