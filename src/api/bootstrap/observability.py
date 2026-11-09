from pydantic import SecretStr

from api.bootstrap.settings import Settings
from api.infrastructure.logging import JsonLogging
from api.infrastructure.tracing import Tracing, UserPseudonym


class Observability:
    @staticmethod
    def start(settings: Settings) -> Tracing:
        JsonLogging.configure()
        return Tracing(
            _reveal(settings.langfuse_public_key),
            _reveal(settings.langfuse_secret_key),
            settings.langfuse_base_url,
            _pseudonym(settings),
        )


def _reveal(secret: SecretStr | None) -> str | None:
    return secret.get_secret_value() if secret else None


def _pseudonym(settings: Settings) -> UserPseudonym | None:
    if settings.jwt_secret is None:
        return None
    return UserPseudonym(settings.jwt_secret.get_secret_value())
