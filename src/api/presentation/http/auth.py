from http import HTTPStatus

from dishka.integrations.fastapi import DishkaRoute, FromDishka
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from api.application.identity.dto.dev_student import DevStudentDto
from api.application.identity.dto.login import LoginDto
from api.application.identity.service import IdentityService
from api.domain.identity.errors import StudentNotFoundError

router = APIRouter(route_class=DishkaRoute)


class DevLoginRequest(BaseModel):
    student: str


@router.post("/auth/dev-login")
async def dev_login(request: DevLoginRequest, service: FromDishka[IdentityService]) -> LoginDto:
    try:
        return await service.login(request.student)
    except StudentNotFoundError:
        raise HTTPException(HTTPStatus.NOT_FOUND, HTTPStatus.NOT_FOUND.phrase) from None


@router.get("/auth/dev-students")
async def dev_students(service: FromDishka[IdentityService]) -> list[DevStudentDto]:
    return await service.dev_students()
