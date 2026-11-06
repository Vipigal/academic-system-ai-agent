from collections.abc import Callable, Sequence

from api.application.agent import agent_errors
from api.application.agent import events as agent_events
from evals.runner import RunListener

SIGNED_VALUE = "valor-assinado-do-aluno"


def proposal_events(
    code: str, answer: str = "Preparei o pedido."
) -> tuple[agent_events.AgentEvent, ...]:
    complete = {
        "status": "ok",
        "data": {"service": {"code": code}, "message": "Pedido"},
        "client_only": {"token": SIGNED_VALUE},
    }
    arguments = {"service": code, "message": "Pedido"}
    return (
        agent_events.ToolCallRequested("1", "propose_protocol", arguments),
        agent_events.ToolResultReceived("1", "propose_protocol", "ok", "{}", complete, 7),
        *answer_events(answer),
    )


def answer_events(
    answer: str, stop_reason: agent_events.StopReason = agent_events.StopReason.COMPLETED
) -> tuple[agent_events.AgentEvent, ...]:
    return (
        agent_events.TextDelta(answer),
        agent_events.AgentFinished(answer, stop_reason, agent_events.TokenUsage(1000, 200)),
    )


class ScriptedDriver:
    def __init__(
        self,
        script: Callable[[str], Sequence[agent_events.AgentEvent] | None],
        trace_id: str | None = None,
    ) -> None:
        self._script = script
        self._trace_id = trace_id
        self.asked: list[str] = []

    async def run(self, student: str, question: str, listener: RunListener) -> None:
        self.asked.append(question)
        if self._trace_id is not None:
            listener.bind_trace(self._trace_id)
        events = self._script(question)
        if events is None:
            raise agent_errors.AgentTimeoutError(student)
        for event in events:
            listener.receive(event)
