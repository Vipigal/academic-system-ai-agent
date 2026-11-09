from typing import Self

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, EnvSettingsSource, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="APP_")

    database_url: SecretStr
    db_pool_size: int = 20
    db_max_overflow: int = 10
    db_pool_timeout_seconds: float = 5

    redis_url: SecretStr | None = None
    chat_rate_limit_per_hour: int = 60

    agent_model: str = "gpt-6-luna"
    agent_effort: str = "low"
    openai_api_key: SecretStr | None = Field(default=None, validation_alias="OPENAI_API_KEY")
    agent_model_call_limit: int = 8
    agent_tool_call_limit: int = 12
    agent_timeout_seconds: float = 60
    agent_max_concurrency: int = 8
    history_window: int = 20

    jwt_secret: SecretStr | None = None
    jwt_ttl_minutes: int = 60
    dev_login: bool = False
    proposal_secret: SecretStr | None = None
    proposal_ttl_minutes: int = 15

    cors_origins: list[str] = ["http://localhost:5173"]

    langfuse_public_key: SecretStr | None = Field(
        default=None, validation_alias="LANGFUSE_PUBLIC_KEY"
    )
    langfuse_secret_key: SecretStr | None = Field(
        default=None, validation_alias="LANGFUSE_SECRET_KEY"
    )
    langfuse_base_url: str | None = Field(default=None, validation_alias="LANGFUSE_BASE_URL")

    @classmethod
    def from_environment(cls) -> Self:
        return cls.model_validate(EnvSettingsSource(cls)())
