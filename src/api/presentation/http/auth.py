from http import HTTPStatus

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from api.application.identity.dto.login import LoginDto
from api.application.identity.service import IdentityService
from api.domain.identity.errors import StudentNotFoundError


class DevLoginRequest(BaseModel):
    student: str


class AuthRouter:
    @staticmethod
    def build(service: IdentityService) -> APIRouter:
        router = APIRouter()

        @router.post("/auth/dev-login")
        async def dev_login(request: DevLoginRequest) -> LoginDto:
            try:
                return await service.login(request.student)
            except StudentNotFoundError:
                raise HTTPException(HTTPStatus.NOT_FOUND, HTTPStatus.NOT_FOUND.phrase) from None

        return router
