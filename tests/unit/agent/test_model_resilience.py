import asyncio
import time
from collections.abc import Sequence
from threading import Lock

import pytest
from langchain_core.messages import AIMessage, BaseMessage
from pydantic import Field

from api.application.agent.agent_errors import AgentFailedError
from api.application.agent.student_agent import StudentAgent
from tests.unit.agent import agent_support as support


class CountingModel(support.RecordingModel):
    lock: Lock = Field(default_factory=Lock, exclude=True)
    active: list[int] = Field(default_factory=list)
    peaks: list[int] = Field(default_factory=list)

    def _next_of(self, messages: Sequence[BaseMessage]) -> AIMessage:
        with self.lock:
            self.active.append(1)
            self.peaks.append(len(self.active))
        time.sleep(0.02)
        with self.lock:
            self.active.pop()
        return super()._next_of(messages)


async def test_a_transient_provider_failure_is_retried() -> None:
    run = await support.agent_with(support.FlakyModel(responses=[support.answer()])).run("Teste")

    assert run.text == support.FINAL_ANSWER


async def test_a_permanent_provider_failure_raises_an_application_error() -> None:
    model = support.FlakyModel(responses=[support.answer()], failures_left=10)

    with pytest.raises(AgentFailedError):
        await support.agent_with(model).run("Teste")


async def test_the_gate_limits_the_simultaneous_calls_to_the_provider() -> None:
    model = CountingModel(responses=[support.answer()])
    runtime = support.runtime_with(model, support.limits_with(max_concurrency=1))

    await asyncio.gather(
        *(StudentAgent(runtime, (), f"trace-{number}").run("Oi") for number in range(4))
    )

    assert len(model.peaks) == 4
    assert max(model.peaks) == 1
