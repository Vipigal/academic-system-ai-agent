from dataclasses import dataclass
from typing import Self


@dataclass(frozen=True, slots=True)
class RateLimitDecision:
    allowed: bool
    limit: int
    remaining: int
    reset_after_seconds: int

    @classmethod
    def counted(cls, count: int, limit: int, reset_after_seconds: int) -> Self:
        return cls(
            allowed=count <= limit,
            limit=limit,
            remaining=max(limit - count, 0),
            reset_after_seconds=max(reset_after_seconds, 0),
        )

    @classmethod
    def unmetered(cls) -> Self:
        return cls(allowed=True, limit=0, remaining=0, reset_after_seconds=0)

    @property
    def metered(self) -> bool:
        return self.limit > 0
