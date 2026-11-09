from dishka import AsyncContainer

from api.application.agent.agent_errors import AgentFailedError
from api.application.agent.agent_runtime import AgentRuntime
from api.bootstrap.containers import Containers, Given
from api.bootstrap.session_providers import PersonId
from api.bootstrap.settings import Settings
from api.domain.identity.session import StudentSession
from api.domain.ports.clock import Clock
from api.domain.ports.identity import PersonDirectory, StudentSessionLoader
from api.infrastructure.clock import FixedClock
from evals.dataset.tool_names import ToolNames
from evals.records import RunVersions

KEY_SEPARATOR = ":"


class EvalContainer:
    @staticmethod
    def create(settings: Settings, given: Given | None = None) -> AsyncContainer:
        return Containers.students(settings, {Clock: FixedClock(), **(given or {})})

    @staticmethod
    def versions_of(container: AsyncContainer, settings: Settings) -> RunVersions:
        runtime = container.get_sync(AgentRuntime)
        return RunVersions(
            model=settings.agent_model,
            effort=settings.agent_effort,
            prompt_version=runtime.prompt.version,
            skills_hash=runtime.skills.fingerprint(),
            tools_hash=ToolNames.fingerprint(),
        )

    @staticmethod
    async def context_of(container: AsyncContainer, student: str) -> Given:
        brand, student_id = student.split(KEY_SEPARATOR, maxsplit=1)
        person_id = await (await container.get(PersonDirectory)).person_of(brand, student_id)
        if person_id is None:
            raise AgentFailedError(f"Aluno sem pessoa na base: {student}")
        session = await (await container.get(StudentSessionLoader)).load(person_id)
        return {StudentSession: session, PersonId: PersonId(person_id)}
