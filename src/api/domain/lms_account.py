from dataclasses import dataclass
from datetime import datetime
from typing import Self


@dataclass(frozen=True, slots=True)
class LmsAccount:
    enrollment: str
    exists: bool
    suspended: bool
    last_access: datetime | None

    @classmethod
    def missing(cls, enrollment: str) -> Self:
        return cls(enrollment=enrollment, exists=False, suspended=False, last_access=None)

    @property
    def never_accessed(self) -> bool:
        return self.exists and self.last_access is None
