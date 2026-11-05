from typing import Self

from pydantic import SecretStr
from pydantic_settings import BaseSettings, EnvSettingsSource, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="APP_")

    database_url: SecretStr

    @classmethod
    def from_environment(cls) -> Self:
        return cls.model_validate(EnvSettingsSource(cls)())
