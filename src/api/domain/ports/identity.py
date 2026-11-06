from typing import Protocol

from api.domain.identity.session import StudentSession


class StudentSessionLoader(Protocol):
    async def load(self, person_id: str) -> StudentSession: ...
