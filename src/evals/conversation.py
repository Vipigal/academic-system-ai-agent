from collections.abc import AsyncGenerator, Mapping, Sequence
from contextlib import aclosing
from typing import Protocol

from api.application.agent import events
from api.application.agent.agent_errors import AgentFailedError
from api.application.agent.history import (
    PastAssistantMessage,
    PastMessage,
    PastToolCall,
    PastUserMessage,
)
from evals.runner import RunListener


class ConversationAgent(Protocol):
    def stream(
        self, message: str, past: Sequence[PastMessage] = ()
    ) -> AsyncGenerator[events.AgentEvent]: ...


class PriorTurnError(AgentFailedError):
    pass


class PriorTurn:
    def __init__(self, question: str) -> None:
        self._question = question
        self._arguments: dict[str, Mapping[str, object]] = {}
        self._results: list[events.ToolResultReceived] = []
        self._finished: events.AgentFinished | None = None

    def receive(self, event: events.AgentEvent) -> None:
        match event:
            case events.ToolCallRequested():
                self._arguments[event.tool_call_id] = event.arguments
            case events.ToolResultReceived():
                self._results.append(event)
            case events.AgentFinished():
                self._finished = event

    @property
    def finished(self) -> events.AgentFinished:
        if self._finished is None:
            raise PriorTurnError(f"Turno anterior sem resposta final: {self._question}")
        return self._finished

    def messages(self) -> tuple[PastMessage, PastMessage]:
        calls = tuple(
            PastToolCall(
                result.tool_call_id,
                result.tool_name,
                self._arguments.get(result.tool_call_id, {}),
                result.seen_by_model,
            )
            for result in self._results
        )
        return PastUserMessage(self._question), PastAssistantMessage(self.finished.text, calls)


class Conversation:
    @classmethod
    async def play(
        cls,
        agent: ConversationAgent,
        history: Sequence[str],
        question: str,
        listener: RunListener,
    ) -> None:
        past: list[PastMessage] = []
        for earlier in history:
            past.extend(await cls._prior(agent, earlier, tuple(past), listener))
        listener.begin_final_turn()
        await cls._stream(agent, question, tuple(past), listener)

    @classmethod
    async def _prior(
        cls,
        agent: ConversationAgent,
        question: str,
        past: tuple[PastMessage, ...],
        listener: RunListener,
    ) -> tuple[PastMessage, PastMessage]:
        turn = PriorTurn(question)
        await cls._stream(agent, question, past, turn)
        finished = turn.finished
        listener.add_usage(finished.usage.tokens_in, finished.usage.tokens_out)
        if finished.stop_reason is not events.StopReason.COMPLETED:
            reason = finished.stop_reason.value
            raise PriorTurnError(f"Turno anterior parou por {reason}")
        return turn.messages()

    @staticmethod
    async def _stream(
        agent: ConversationAgent,
        question: str,
        past: tuple[PastMessage, ...],
        listener: RunListener | PriorTurn,
    ) -> None:
        async with aclosing(agent.stream(question, past)) as stream:
            async for event in stream:
                listener.receive(event)
