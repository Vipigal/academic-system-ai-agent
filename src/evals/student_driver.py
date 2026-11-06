from uuid import uuid4

from langfuse import observe, propagate_attributes

from api.application.agent.agent_errors import AgentFailedError
from api.bootstrap.chat_agent_scope import ChatAgentScope
from api.bootstrap.singletons import Singletons
from api.infrastructure.logging import trace_id_var
from api.infrastructure.tracing import Tracing
from api.persistence.identity.student_session_repository import StudentSessionRepository
from evals.conversation import Conversation
from evals.records import RunVersions
from evals.runner import RunListener
from evals.trace_links import TraceLinks

EVAL_TAG = "eval"
KEY_SEPARATOR = ":"


class StudentDriver:
    def __init__(self, singletons: Singletons, tracing: Tracing, versions: RunVersions) -> None:
        self.versions = versions
        self.max_concurrency = singletons.settings.agent_max_concurrency
        self._singletons = singletons
        self._tracing = tracing
        self._scope = ChatAgentScope(singletons, tracing)
        self._identities = StudentSessionRepository(singletons.database.db_session_factory)

    def trace_url_prefix(self) -> str | None:
        return TraceLinks.prefix() if self._tracing.enabled else None

    @observe(name="eval.execution", capture_input=False, capture_output=False)
    async def run(
        self, student: str, question: str, history: tuple[str, ...], listener: RunListener
    ) -> None:
        person_id = await self._person_of(student)
        session = await self._identities.load(person_id)
        with (
            propagate_attributes(tags=self._tags_of(self.versions)),
            self._scope.traced_agent(session, person_id, uuid4()) as agent,
        ):
            if self._tracing.enabled:
                listener.bind_trace(trace_id_var.get())
            await Conversation.play(agent, history, question, listener)

    async def close(self) -> None:
        self._tracing.flush()
        await self._singletons.dispose()

    @staticmethod
    def _tags_of(versions: RunVersions) -> list[str]:
        return [EVAL_TAG, f"effort:{versions.effort}", f"tools:{versions.tools_hash}"]

    async def _person_of(self, student: str) -> str:
        brand, student_id = student.split(KEY_SEPARATOR, maxsplit=1)
        person_id = await self._identities.person_of(brand, student_id)
        if person_id is None:
            raise AgentFailedError(f"Aluno sem pessoa na base: {student}")
        return person_id
