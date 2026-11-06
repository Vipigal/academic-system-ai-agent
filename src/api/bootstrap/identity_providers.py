from collections.abc import Awaitable, Callable
from typing import Annotated

from fastapi import APIRouter, Depends

from api.application.identity.service import IdentityService
from api.bootstrap.settings import Settings
from api.domain.identity.session import StudentSession
from api.infrastructure.token_codec import JwtCodec
from api.persistence.core.database import Database
from api.persistence.identity.student_session_repository import StudentSessionRepository
from api.presentation.http.auth import AuthRouter
from api.presentation.http.identity import IdentityDependency, Unauthorized


class IdentityProviders:
    def __init__(self, settings: Settings, database: Database) -> None:
        secret = settings.jwt_secret.get_secret_value() if settings.jwt_secret else ""
        self._settings = settings
        self._repository = StudentSessionRepository(database.db_session_factory)
        self._service = IdentityService(
            self._repository, JwtCodec(secret, settings.jwt_ttl_minutes)
        )
        self._person_id = IdentityDependency.build(self._service)

    @property
    def person_id(self) -> Callable[..., str]:
        return self._person_id

    def auth_router(self) -> APIRouter | None:
        return AuthRouter.build(self._service) if self._settings.dev_login else None

    def session_dependency(self) -> Callable[..., Awaitable[StudentSession]]:
        async def student_session(
            person_id: Annotated[str, Depends(self._person_id)],
        ) -> StudentSession:
            session = await self._repository.load(person_id)
            if not session.person_ids:
                raise Unauthorized
            return session

        return student_session
