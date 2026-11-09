from http import HTTPStatus

from fastapi import HTTPException, Request
from fastapi.security import HTTPBearer

from api.application.identity.service import IdentityService
from api.domain.identity.errors import UnauthenticatedError

BEARER_CHALLENGE = {"WWW-Authenticate": "Bearer"}


class Unauthorized(HTTPException):
    def __init__(self) -> None:
        super().__init__(HTTPStatus.UNAUTHORIZED, HTTPStatus.UNAUTHORIZED.phrase, BEARER_CHALLENGE)


class BearerIdentity:
    _bearer = HTTPBearer(auto_error=False)

    @classmethod
    async def person_of(cls, request: Request, service: IdentityService) -> str:
        credentials = await cls._bearer(request)
        if credentials is None:
            raise Unauthorized
        try:
            return service.authenticate(credentials.credentials)
        except UnauthenticatedError:
            raise Unauthorized from None
