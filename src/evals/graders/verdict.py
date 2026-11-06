from collections.abc import Iterable
from dataclasses import dataclass
from enum import StrEnum
from typing import Self


class GraderName(StrEnum):
    TRAJECTORY = "trajectory"
    REFUSAL = "refusal"
    LEAK = "leak"
    PROPOSAL = "proposal"
    JUDGE = "judge"


@dataclass(frozen=True, slots=True)
class Verdict:
    grader: GraderName
    passed: bool
    problems: tuple[str, ...] = ()

    @classmethod
    def of(cls, grader: GraderName, problems: Iterable[str]) -> Self:
        found = tuple(problems)
        return cls(grader, passed=not found, problems=found)
