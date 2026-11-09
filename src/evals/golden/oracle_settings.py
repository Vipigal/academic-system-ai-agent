from pathlib import Path
from typing import Self

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

from evals.settings_sources import SettingsSources


class OracleSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="APP_")

    oracle_database_url: SecretStr

    @classmethod
    def from_environment(cls, env_file: Path | None = None) -> Self:
        return cls.model_validate(SettingsSources.values(cls, env_file))
