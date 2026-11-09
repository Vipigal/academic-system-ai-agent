from collections.abc import Generator
from contextlib import contextmanager
from uuid import UUID

from api.application.agent.agent_runtime import AgentRuntime
from api.application.agent.student_agent import StudentAgent
from api.application.agent.student_tools import StudentTools
from api.bootstrap.session_providers import PersonId
from api.bootstrap.settings import Settings
from api.infrastructure.logging import trace_id_var
from api.infrastructure.tracing import CurrentTrace, TraceInfo, Tracing


class ChatAgentScope:
    def __init__(
        self,
        tools: StudentTools,
        runtime: AgentRuntime,
        tracing: Tracing,
        settings: Settings,
        person: PersonId,
    ) -> None:
        self._tools = tools
        self._runtime = runtime
        self._tracing = tracing
        self._settings = settings
        self._person = person

    @contextmanager
    def traced_agent(self, conversation: UUID) -> Generator[StudentAgent]:
        CurrentTrace(enabled=self._tracing.enabled).bind_to_log()
        handler = self._tracing.handler()
        with self._tracing.request(self._info_of(conversation)):
            yield StudentAgent(
                self._runtime,
                self._tools.registry().tools,
                trace_id_var.get(),
                (handler,) if handler else (),
            )

    def _info_of(self, conversation: UUID) -> TraceInfo:
        return TraceInfo(
            self._person,
            str(conversation),
            self._settings.agent_model,
            self._runtime.prompt.version,
            self._runtime.skills.fingerprint(),
        )
