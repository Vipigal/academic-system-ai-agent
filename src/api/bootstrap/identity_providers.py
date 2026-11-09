from dishka import AnyOf, Provider, Scope, provide

from api.application.identity.service import IdentityService
from api.bootstrap.settings import Settings
from api.domain.ports.identity import PersonDirectory, StudentSessionLoader, TokenCodec
from api.infrastructure.token_codec import JwtCodec
from api.persistence.identity.student_session_repository import StudentSessionRepository


class IdentityProvider(Provider):
    scope = Scope.APP

    sessions = provide(
        StudentSessionRepository, provides=AnyOf[StudentSessionLoader, PersonDirectory]
    )
    identity = provide(IdentityService)

    @provide
    def codec(self, settings: Settings) -> TokenCodec:
        secret = settings.jwt_secret.get_secret_value() if settings.jwt_secret else ""
        return JwtCodec(secret, settings.jwt_ttl_minutes)
