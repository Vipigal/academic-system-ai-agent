from collections.abc import Mapping
from dataclasses import dataclass, field

FAILED_STATUSES = frozenset({"invalid", "error"})
COMPLETED = "completed"


@dataclass(frozen=True, slots=True)
class ToolStep:
    name: str
    arguments: Mapping[str, object]
    status: str
    duration_ms: int
    output: Mapping[str, object] = field(default_factory=dict)
    guardrail_problems: tuple[str, ...] = ()

    @property
    def succeeded(self) -> bool:
        return self.status not in FAILED_STATUSES


@dataclass(frozen=True, slots=True)
class Usage:
    tokens_in: int = 0
    tokens_out: int = 0


@dataclass(frozen=True, slots=True)
class Timing:
    total_ms: float
    first_token_ms: float | None


@dataclass(frozen=True, slots=True)
class Execution:
    item_id: str
    epoch: int
    question: str
    answer: str
    steps: tuple[ToolStep, ...] = ()
    stop_reason: str = COMPLETED
    timing: Timing = Timing(0, None)
    usage: Usage = Usage()
    error: str | None = None
    trace_id: str | None = None

    @property
    def failure(self) -> str | None:
        if self.error is not None or self.stop_reason == COMPLETED:
            return self.error
        return self.stop_reason

    @property
    def key(self) -> str:
        return f"{self.item_id}#{self.epoch}"

    @property
    def tools_used(self) -> frozenset[str]:
        return frozenset(step.name for step in self.steps if step.succeeded)

    @property
    def tools_called(self) -> frozenset[str]:
        return frozenset(step.name for step in self.steps)
