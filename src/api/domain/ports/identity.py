from typing import Protocol

from api.domain.identity.session import StudentSession


class StudentSessionLoader(Protocol):
    async def load(self, person_id: str) -> StudentSession: ...


class PersonDirectory(Protocol):
    async def person_of(self, brand: str, student_id: str) -> str | None: ...


class TokenCodec(Protocol):
    def issue(self, person_id: str) -> str: ...

    def person_of(self, token: str) -> str | None: ...
