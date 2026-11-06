from collections.abc import Generator
from contextlib import contextmanager
from uuid import UUID

from api.application.agent.student_agent import StudentAgent
from api.bootstrap.protocol_providers import ProtocolProviders
from api.bootstrap.singletons import Singletons
from api.bootstrap.student_providers import StudentProviders
from api.bootstrap.tool_providers import ToolProviders
from api.domain.identity.session import StudentSession
from api.infrastructure.logging import trace_id_var
from api.infrastructure.tracing import CurrentTrace, TraceInfo, Tracing


class ChatAgentScope:
    def __init__(self, singletons: Singletons, tracing: Tracing) -> None:
        signer = ProtocolProviders.signer_of(singletons.settings)
        self._singletons = singletons
        self._tracing = tracing
        self._students = StudentProviders(singletons.database, singletons.clock, signer)

    @contextmanager
    def traced_agent(
        self, session: StudentSession, person_id: str, conversation: UUID
    ) -> Generator[StudentAgent]:
        CurrentTrace(enabled=self._tracing.enabled).bind_to_log()
        handler = self._tracing.handler()
        tools = ToolProviders.tools_for(self._students.services_for(session))
        with self._tracing.request(self._info_of(person_id, conversation)):
            yield self._singletons.agent.agent_for(
                tools, trace_id_var.get(), (handler,) if handler else ()
            )

    def _info_of(self, person_id: str, conversation: UUID) -> TraceInfo:
        runtime = self._singletons.agent.runtime
        return TraceInfo(
            person_id,
            str(conversation),
            self._singletons.settings.agent_model,
            runtime.prompt.version,
            runtime.skills.fingerprint(),
        )
