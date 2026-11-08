from collections.abc import Mapping
from dataclasses import dataclass
from enum import Enum
from typing import Self, get_args

from pydantic import ConfigDict, Field

from api.application.agent.tools.registry import ToolContractError
from api.application.shared.page import DEFAULT_LIMIT, MAX_LIMIT, PageRequest
from api.application.shared.period_filter import PERIOD_FORMAT

MIN_LIMIT = 1
MIN_OFFSET = 0
LIST_SEPARATOR = ", "


class BoundedPage(PageRequest):
    model_config = ConfigDict(extra="forbid")

    offset: int = Field(default=MIN_OFFSET, ge=MIN_OFFSET)
    limit: int = Field(default=DEFAULT_LIMIT, ge=MIN_LIMIT, le=MAX_LIMIT)


@dataclass(frozen=True, slots=True)
class ParameterGuide:
    accepted: str
    example: str
    pattern: str | None = None

    @classmethod
    def of_enum(cls, enum_type: type[Enum]) -> Self:
        values = [str(member.value) for member in enum_type]
        return cls(accepted=f"um destes valores: {LIST_SEPARATOR.join(values)}", example=values[0])

    @classmethod
    def of_parameter(cls, name: str, annotation: object) -> ParameterGuide:
        for hint in (annotation, *get_args(annotation)):
            if isinstance(hint, type) and issubclass(hint, Enum):
                return ParameterGuide.of_enum(hint)
        guide = GUIDES.get(name)
        if guide is None:
            raise ToolContractError(f"O parâmetro {name} não tem texto de ensino")
        return guide


GUIDES: Mapping[str, ParameterGuide] = {
    "term": ParameterGuide("o semestre no formato AAAA/S", "2026/2", r"^\d{4}/[12]$"),
    "period": ParameterGuide(
        "o ano AAAA ou o mês AAAA-MM", "2026-10", f"^{PERIOD_FORMAT.pattern}$"
    ),
    "enrollment": ParameterGuide(
        "a matrícula no formato marca:RA, como vem em list_enrollments",
        "UniSaoPaulo:000000",
        r"^[^:\s]+:[^:\s]+$",
    ),
    "course": ParameterGuide("o nome do curso, em texto", "Enfermagem"),
    "unit": ParameterGuide("o nome da unidade, em texto", "Campus Paulista"),
    "semester": ParameterGuide("o número do semestre da matriz, inteiro", "3"),
    "subject": ParameterGuide("o código ou o nome da disciplina, em texto", "ADM0104"),
    "pending_only": ParameterGuide("true ou false", "true"),
    "filters": ParameterGuide(
        "um objeto com semester, subject e pending_only, todos opcionais",
        '{"semester": 3, "pending_only": true}',
    ),
    "show_ui": ParameterGuide("true ou false", "true"),
    "page": ParameterGuide("um objeto com offset e limit", '{"offset": 0, "limit": 20}'),
    "offset": ParameterGuide(f"um inteiro a partir de {MIN_OFFSET}", str(MIN_OFFSET)),
    "limit": ParameterGuide(f"um inteiro de {MIN_LIMIT} a {MAX_LIMIT}", str(DEFAULT_LIMIT)),
    "year": ParameterGuide("o ano com quatro dígitos, inteiro", "2026"),
    "service": ParameterGuide("o código do serviço, em texto", "DOC-001"),
    "number": ParameterGuide("o número do protocolo, em texto", "20260024630"),
    "message": ParameterGuide("o texto do pedido", "Preciso de uma declaração de matrícula."),
    "query": ParameterGuide("um trecho do título do material", "Semana 2"),
}
