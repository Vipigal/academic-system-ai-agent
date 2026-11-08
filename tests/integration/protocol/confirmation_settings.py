import secrets

from pydantic import SecretStr

from api.bootstrap.settings import Settings

JWT_SECRET = secrets.token_urlsafe(32)
PROPOSAL_SECRET = secrets.token_urlsafe(32)


def settings_with(**overrides: object) -> Settings:
    updates = {
        "jwt_secret": SecretStr(JWT_SECRET),
        "proposal_secret": SecretStr(PROPOSAL_SECRET),
        "dev_login": True,
        **overrides,
    }
    return Settings.from_environment().model_copy(update=updates)
