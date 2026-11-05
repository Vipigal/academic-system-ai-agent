from collections.abc import Sequence
from typing import Protocol

from api.domain.lms import OnlineExam
from api.domain.lms_account import LmsAccount
from api.domain.lms_material import CourseMaterial


class LmsRepository(Protocol):
    async def list_exams(self) -> Sequence[OnlineExam]: ...

    async def list_accounts(self) -> Sequence[LmsAccount]: ...

    async def list_materials(self) -> Sequence[CourseMaterial]: ...
