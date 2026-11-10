from http import HTTPStatus

from fastapi import HTTPException, Request, Security
from fastapi.requests import HTTPConnection
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from api.application.identity.service import IdentityService
from api.domain.identity.errors import UnauthenticatedError

BEARER_CHALLENGE = {"WWW-Authenticate": "Bearer"}


class Unauthorized(HTTPException):
    def __init__(self) -> None:
        super().__init__(HTTPStatus.UNAUTHORIZED, HTTPStatus.UNAUTHORIZED.phrase, BEARER_CHALLENGE)


class RequiredBearer(HTTPBearer):
    def __init__(self) -> None:
        super().__init__(scheme_name="HTTPBearer", auto_error=False)

    async def __call__(self, request: HTTPConnection) -> HTTPAuthorizationCredentials:
        credentials = await super().__call__(request)
        if credentials is None:
            raise Unauthorized
        return credentials


REQUIRED_BEARER = Security(RequiredBearer())


class BearerIdentity:
    _bearer = RequiredBearer()

    @classmethod
    async def person_of(cls, request: Request, service: IdentityService) -> str:
        credentials = await cls._bearer(request)
        try:
            return service.authenticate(credentials.credentials)
        except UnauthenticatedError:
            raise Unauthorized from None
