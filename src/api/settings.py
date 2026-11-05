from datetime import date
from typing import Self

from pydantic import SecretStr
from pydantic_settings import BaseSettings, EnvSettingsSource, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="APP_")

    database_url: SecretStr
    reference_date: date = date(2026, 10, 31)

    @classmethod
    def from_environment(cls) -> Self:
        return cls.model_validate(EnvSettingsSource(cls)())


class ReferenceClock:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    def today(self) -> date:
        return self._settings.reference_date
