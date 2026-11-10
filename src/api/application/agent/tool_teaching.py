import json
from collections.abc import Sequence

from pydantic import BaseModel, ValidationError
from pydantic_core import ErrorDetails

from api.application.agent.tool_arguments import LIST_SEPARATOR, PATH_SEPARATOR, ToolArguments

MAX_ECHOED_INPUT = 80
MISSING = "missing"
UNKNOWN_PARAMETER = "extra_forbidden"


class ToolTeaching:
    def __init__(self, name: str, arguments: type[BaseModel]) -> None:
        self._name = name
        self._arguments = arguments
        for parameter in arguments.model_fields:
            ToolArguments.teaching_at(arguments, (parameter,))

    def paragraph(self, error: ValidationError) -> str:
        sentences = {
            self._path(detail["loc"]): self._sentence(detail)
            for detail in error.errors(include_url=False, include_context=False)
        }
        lines = " ".join(sentences.values())
        return f"A chamada de {self._name} não foi executada. {lines} Corrija e chame de novo."

    def _sentence(self, detail: ErrorDetails) -> str:
        path = self._path(detail["loc"])
        if detail["type"] == UNKNOWN_PARAMETER:
            return f"O parâmetro `{path}` não existe nesta tool. {self._accepted_parameters()}"
        teaching = ToolArguments.teaching_at(self._arguments, detail["loc"])
        if detail["type"] == MISSING:
            opening = f"O parâmetro `{path}` é obrigatório e não veio."
        else:
            echoed = json.dumps(detail["input"], ensure_ascii=False, default=str)
            shown = echoed[:MAX_ECHOED_INPUT]
            opening = f"O parâmetro `{path}` veio como {shown}."
        return f"{opening} Aceita {teaching.accepted}. Exemplo: {teaching.example}."

    def _accepted_parameters(self) -> str:
        names = LIST_SEPARATOR.join(self._arguments.model_fields)
        if names:
            return f"Os parâmetros aceitos são: {names}."
        return "Esta tool não recebe parâmetros; chame com {}."

    @staticmethod
    def _path(loc: Sequence[str | int]) -> str:
        return PATH_SEPARATOR.join(map(str, loc))
