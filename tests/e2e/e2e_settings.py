from api.bootstrap.settings import Settings
from tests.integration.chat.chat_settings import settings_with


def e2e_settings(**overrides: object) -> Settings:
    return settings_with(langfuse_public_key=None, langfuse_secret_key=None, **overrides)


def live_settings() -> Settings:
    model = Settings.from_environment().agent_model
    return e2e_settings(agent_model=model)
