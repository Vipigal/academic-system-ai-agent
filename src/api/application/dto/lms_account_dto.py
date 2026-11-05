from datetime import datetime
from typing import Self

from pydantic import BaseModel, ConfigDict

from api.domain.lms_account import LmsAccount


class LmsAccountDto(BaseModel):
    model_config = ConfigDict(frozen=True)

    enrollment: str
    exists: bool
    suspended: bool | None
    never_accessed: bool | None
    last_access: datetime | None

    @classmethod
    def from_entity(cls, account: LmsAccount) -> Self:
        if not account.exists:
            return cls(
                enrollment=account.enrollment,
                exists=False,
                suspended=None,
                never_accessed=None,
                last_access=None,
            )
        return cls(
            enrollment=account.enrollment,
            exists=True,
            suspended=account.suspended,
            never_accessed=account.never_accessed,
            last_access=account.last_access,
        )
