import secrets
from pathlib import Path

from dishka import AsyncContainer
from pydantic import SecretStr

from api.bootstrap.containers import Given
from api.bootstrap.settings import Settings
from api.infrastructure.logging import JsonLogging
from evals.eval_container import EvalContainer
from evals.settings_sources import SettingsSources
from evals.student_driver import StudentDriver


class DriverFactory:
    @staticmethod
    def settings_for(model: str, effort: str, env_file: Path | None = None) -> Settings:
        environment = Settings.model_validate(SettingsSources.values(Settings, env_file))
        return environment.model_copy(
            update={
                "agent_model": model,
                "agent_effort": effort,
                "proposal_secret": SecretStr(secrets.token_hex()),
            }
        )

    @staticmethod
    def container_for(settings: Settings, given: Given | None = None) -> AsyncContainer:
        return EvalContainer.create(settings, given)

    @staticmethod
    def create(settings: Settings) -> StudentDriver:
        JsonLogging.configure()
        container = EvalContainer.create(settings)
        return StudentDriver(container, EvalContainer.versions_of(container, settings))
