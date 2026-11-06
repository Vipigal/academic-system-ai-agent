import asyncio
import logging
from collections.abc import AsyncIterator, Sequence

from langchain.agents.middleware.model_call_limit import ModelCallLimitExceededError
from langchain_core.callbacks import BaseCallbackHandler

from api.application.agent import agent_messages, events, history
from api.application.agent.agent_errors import AgentFailedError, AgentTimeoutError
from api.application.agent.agent_graph import AgentGraph, GraphPart
from api.application.agent.agent_runtime import AgentRuntime
from api.application.agent.agent_stream import StreamTranslator
from api.application.agent.tools.registry import RegisteredTool, ToolRegistry
from api.application.agent.tools.skill_tools import SkillTools

logger = logging.getLogger(__name__)


class StudentAgent:
    def __init__(
        self,
        runtime: AgentRuntime,
        tools: Sequence[RegisteredTool],
        trace_id: str,
        callbacks: Sequence[BaseCallbackHandler] = (),
    ) -> None:
        skill_tools = ToolRegistry(SkillTools(runtime.skills)).tools
        self._graph = AgentGraph(runtime, (*tools, *skill_tools), trace_id)
        self._timeout_seconds = runtime.limits.timeout_seconds
        self._trace_id = trace_id
        self._callbacks = list(callbacks)

    async def stream(
        self, message: str, past: Sequence[history.PastMessage] = ()
    ) -> AsyncIterator[events.AgentEvent]:
        translator = StreamTranslator()
        stop_reason = events.StopReason.COMPLETED
        try:
            async for part in self._bounded(self._parts_of(message, past)):
                for event in translator.translate(part["type"], part["data"]):
                    yield event
        except ModelCallLimitExceededError:
            stop_reason = events.StopReason.MODEL_CALL_LIMIT
        except AgentTimeoutError:
            raise
        except Exception as error:
            logger.exception("Falha do agente", extra={"trace_id": self._trace_id})
            raise AgentFailedError("A execução do agente falhou") from error
        for event in translator.closing(stop_reason):
            yield event

    async def run(self, message: str, past: Sequence[history.PastMessage] = ()) -> events.AgentRun:
        collected = [event async for event in self.stream(message, past)]
        finished = collected[-1]
        if not isinstance(finished, events.AgentFinished):
            raise AgentFailedError("A execução terminou sem o evento final")
        return events.AgentRun(
            finished.text, finished.stop_reason, finished.usage, tuple(collected)
        )

    def _parts_of(
        self, message: str, past: Sequence[history.PastMessage]
    ) -> AsyncIterator[GraphPart]:
        return self._graph.parts(
            agent_messages.AgentMessages.of(past, message),
            {"callbacks": self._callbacks, "metadata": {"trace_id": self._trace_id}},
        )

    async def _bounded[T](self, parts: AsyncIterator[T]) -> AsyncIterator[T]:
        deadline = asyncio.get_running_loop().time() + self._timeout_seconds
        while True:
            try:
                async with asyncio.timeout_at(deadline):
                    part = await anext(parts)
            except StopAsyncIteration:
                return
            except TimeoutError as error:
                raise AgentTimeoutError("A execução passou do tempo limite") from error
            yield part
