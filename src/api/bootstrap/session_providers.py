from typing import NewType

from dishka import Provider, Scope, from_context, provide
from fastapi import Request

from api.application.identity.service import IdentityService
from api.domain.identity.session import StudentSession
from api.domain.ports.identity import StudentSessionLoader
from api.presentation.http.identity import BearerIdentity, Unauthorized

PersonId = NewType("PersonId", str)


class HttpSession(Provider):
    scope = Scope.REQUEST

    request = from_context(provides=Request)

    @provide
    async def person(self, request: Request, identity: IdentityService) -> PersonId:
        return PersonId(await BearerIdentity.person_of(request, identity))

    @provide
    async def session(self, person: PersonId, loader: StudentSessionLoader) -> StudentSession:
        session = await loader.load(person)
        if not session.person_ids:
            raise Unauthorized
        return session


class GivenSession(Provider):
    scope = Scope.REQUEST

    person = from_context(provides=PersonId)
    session = from_context(provides=StudentSession)
