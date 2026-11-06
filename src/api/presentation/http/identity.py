from collections.abc import Callable
from http import HTTPStatus
from typing import Annotated

from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from api.application.identity.service import IdentityService
from api.domain.identity.errors import UnauthenticatedError

BEARER_CHALLENGE = {"WWW-Authenticate": "Bearer"}


class Unauthorized(HTTPException):
    def __init__(self) -> None:
        super().__init__(HTTPStatus.UNAUTHORIZED, HTTPStatus.UNAUTHORIZED.phrase, BEARER_CHALLENGE)


class IdentityDependency:
    @staticmethod
    def build(service: IdentityService) -> Callable[..., str]:
        bearer = HTTPBearer(auto_error=False)

        def person_id(
            credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)],
        ) -> str:
            if credentials is None:
                raise Unauthorized
            try:
                return service.authenticate(credentials.credentials)
            except UnauthenticatedError:
                raise Unauthorized from None

        return person_id
