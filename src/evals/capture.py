import time
from collections.abc import Mapping

from api.application.agent.events import (
    AgentEvent,
    AgentFinished,
    TextDelta,
    TokenUsage,
    ToolCallRequested,
    ToolResultReceived,
)
from evals.execution import Execution, Timing, ToolStep, Usage
from evals.graders.proposal import ConfirmationGuardrail, ProposalOutput

CLIENT_ONLY = "client_only"
MILLISECONDS = 1000


class ToolSteps:
    @staticmethod
    def of(result: ToolResultReceived, arguments: Mapping[str, object]) -> ToolStep:
        complete = result.complete
        output = {key: complete[key] for key in complete if key != CLIENT_ONLY}
        guardrail = (
            ConfirmationGuardrail.problems_of(complete)
            if ProposalOutput.is_valid_proposal(result.tool_name, result.status)
            else ()
        )
        return ToolStep(
            result.tool_name, arguments, result.status, result.duration_ms, output, guardrail
        )


class TurnClock:
    def __init__(self) -> None:
        self._started = time.perf_counter()
        self._first_token_ms: float | None = None

    @property
    def first_token_ms(self) -> float | None:
        return self._first_token_ms

    def elapsed_ms(self) -> float:
        return (time.perf_counter() - self._started) * MILLISECONDS

    def mark_first_token(self) -> None:
        if self._first_token_ms is None:
            self._first_token_ms = self.elapsed_ms()


class SpentUsage:
    def __init__(self) -> None:
        self._tokens_in = 0
        self._tokens_out = 0

    def add(self, tokens_in: int, tokens_out: int) -> None:
        self._tokens_in += tokens_in
        self._tokens_out += tokens_out

    def with_last(self, finished: AgentFinished | None) -> Usage:
        last = finished.usage if finished else TokenUsage()
        return Usage(self._tokens_in + last.tokens_in, self._tokens_out + last.tokens_out)


class ExecutionRecorder:
    def __init__(self, item_id: str, repetition: int, question: str) -> None:
        self._identity = (item_id, repetition, question)
        self._clock = TurnClock()
        self._spent = SpentUsage()
        self._arguments: dict[str, Mapping[str, object]] = {}
        self._steps: list[ToolStep] = []
        self._finished: AgentFinished | None = None
        self._trace_id: str | None = None

    def bind_trace(self, trace_id: str) -> None:
        self._trace_id = trace_id

    def begin_final_turn(self) -> None:
        self._clock = TurnClock()

    def add_usage(self, tokens_in: int, tokens_out: int) -> None:
        self._spent.add(tokens_in, tokens_out)

    def receive(self, event: AgentEvent) -> None:
        match event:
            case TextDelta():
                self._clock.mark_first_token()
            case ToolCallRequested():
                self._arguments[event.tool_call_id] = event.arguments
            case ToolResultReceived():
                arguments = self._arguments.get(event.tool_call_id, {})
                self._steps.append(ToolSteps.of(event, arguments))
            case AgentFinished():
                self._finished = event

    def finish(self, error: str | None = None) -> Execution:
        item_id, repetition, question = self._identity
        finished = self._finished
        return Execution(
            item_id,
            repetition,
            question,
            finished.text if finished else "",
            tuple(self._steps),
            finished.stop_reason.value if finished else "failed",
            Timing(self._clock.elapsed_ms(), self._clock.first_token_ms),
            self._spent.with_last(finished),
            error,
            self._trace_id,
        )
