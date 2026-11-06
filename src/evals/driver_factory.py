import secrets

from pydantic import SecretStr

from api.bootstrap.observability import Observability
from api.bootstrap.settings import Settings
from api.bootstrap.singletons import Singletons
from evals.golden.tool_names import ToolNames
from evals.records import RunVersions
from evals.student_driver import StudentDriver


class DriverFactory:
    @staticmethod
    def settings_for(model: str, effort: str) -> Settings:
        return Settings.from_environment().model_copy(
            update={
                "agent_model": model,
                "agent_effort": effort,
                "proposal_secret": SecretStr(secrets.token_hex()),
            }
        )

    @staticmethod
    def create(settings: Settings) -> StudentDriver:
        singletons = Singletons.create(settings)
        runtime = singletons.agent.runtime
        versions = RunVersions(
            model=settings.agent_model,
            effort=settings.agent_effort,
            prompt_version=runtime.prompt.version,
            skills_hash=runtime.skills.fingerprint(),
            tools_hash=ToolNames.fingerprint(),
        )
        return StudentDriver(singletons, Observability.start(settings), versions)
