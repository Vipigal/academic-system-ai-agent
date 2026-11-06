import secrets

from pydantic import SecretStr

from api.bootstrap.settings import Settings

TEST_MODEL = "modelo-de-teste"


def settings_with(**overrides: object) -> Settings:
    updates = {
        "jwt_secret": SecretStr(secrets.token_urlsafe(32)),
        "proposal_secret": SecretStr(secrets.token_urlsafe(32)),
        "dev_login": True,
        "agent_model": TEST_MODEL,
        **overrides,
    }
    return Settings.from_environment().model_copy(update=updates)
