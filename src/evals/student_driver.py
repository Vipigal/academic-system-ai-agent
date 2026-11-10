from uuid import uuid4

from dishka import AsyncContainer
from langfuse import observe, propagate_attributes

from api.bootstrap.chat_agent_scope import ChatAgentScope
from api.infrastructure.logging import trace_id_var
from api.infrastructure.tracing import Tracing
from evals.conversation import Conversation
from evals.eval_container import EvalContainer
from evals.records import RunVersions
from evals.runner import RunListener
from evals.trace_links import TraceLinks

EVAL_TAG = "eval"


class StudentDriver:
    def __init__(self, container: AsyncContainer, versions: RunVersions) -> None:
        self.versions = versions
        self._container = container
        self._tracing = container.get_sync(Tracing)

    def trace_url_prefix(self) -> str | None:
        return TraceLinks.prefix() if self._tracing.enabled else None

    @observe(name="eval.execution", capture_input=False, capture_output=False)
    async def run(
        self, student: str, question: str, history: tuple[str, ...], listener: RunListener
    ) -> None:
        context = await EvalContainer.context_of(self._container, student)
        async with self._container(context=context) as request:
            scope = await request.get(ChatAgentScope)
            with (
                propagate_attributes(tags=self._tags_of(self.versions)),
                scope.traced_agent(uuid4()) as agent,
            ):
                if self._tracing.enabled:
                    listener.bind_trace(trace_id_var.get())
                await Conversation.play(agent, history, question, listener)

    async def close(self) -> None:
        self._tracing.flush()
        await self._container.close()

    @staticmethod
    def _tags_of(versions: RunVersions) -> list[str]:
        return [EVAL_TAG, f"effort:{versions.effort}", f"tools:{versions.tools_hash}"]
