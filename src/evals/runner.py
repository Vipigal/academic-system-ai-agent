import asyncio
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Protocol

from api.application.agent.agent_errors import AgentFailedError
from api.application.agent.events import AgentEvent
from evals.capture import ExecutionRecorder
from evals.execution import Execution
from evals.graders.suite import GraderSuite
from evals.graders.verdict import Verdict
from evals.item_context import ItemContext


class RunListener(Protocol):
    def receive(self, event: AgentEvent) -> None: ...

    def bind_trace(self, trace_id: str) -> None: ...


class AgentDriver(Protocol):
    async def run(self, student: str, question: str, listener: RunListener) -> None: ...


class ExecutionSink(Protocol):
    def record(
        self, context: ItemContext, execution: Execution, verdicts: Sequence[Verdict]
    ) -> None: ...


@dataclass(frozen=True, slots=True)
class ContextualizedExecution:
    context: ItemContext
    repetition: int


class EvalRunner:
    def __init__(self, driver: AgentDriver, sink: ExecutionSink, concurrency: int) -> None:
        self._driver = driver
        self._sink = sink
        self._gate = asyncio.Semaphore(concurrency)

    async def run(self, planned: Sequence[ContextualizedExecution]) -> None:
        async with asyncio.TaskGroup() as group:
            for execution in planned:
                group.create_task(self._one(execution))

    async def _one(self, planned: ContextualizedExecution) -> None:
        async with self._gate:
            execution = await self._executed(planned)
        verdicts = GraderSuite.grade(planned.context, execution)
        self._sink.record(planned.context, execution, verdicts)

    async def _executed(self, planned: ContextualizedExecution) -> Execution:
        context = planned.context
        recorder = ExecutionRecorder(context.item.id, planned.repetition, context.question)
        try:
            await self._driver.run(context.item.student, context.question, recorder)
        except AgentFailedError as error:
            return recorder.finish(type(error).__name__)
        return recorder.finish()
