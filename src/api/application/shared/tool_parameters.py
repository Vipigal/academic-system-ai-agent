from dataclasses import dataclass
from typing import Annotated

from pydantic import Field

from api.application.shared.period_filter import PERIOD_FORMAT


@dataclass(frozen=True, slots=True)
class Teaching:
    accepted: str
    example: str


TermArgument = Annotated[
    str,
    Field(pattern=r"^\d{4}/[12]$"),
    Teaching("o semestre no formato AAAA/S", "2026/2"),
]
PeriodArgument = Annotated[
    str,
    Field(pattern=f"^{PERIOD_FORMAT.pattern}$"),
    Teaching("o ano AAAA ou o mês AAAA-MM", "2026-10"),
]
EnrollmentArgument = Annotated[
    str,
    Field(pattern=r"^[^:\s]+:[^:\s]+$"),
    Teaching("a matrícula no formato marca:RA, como vem em list_enrollments", "UniSaoPaulo:000000"),
]
SubjectArgument = Annotated[str, Teaching("o código ou o nome da disciplina, em texto", "ADM0104")]
FlagArgument = Annotated[bool, Teaching("true ou false", "true")]
