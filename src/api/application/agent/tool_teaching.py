import json

from pydantic import ValidationError
from pydantic_core import ErrorDetails

from api.application.agent.tool_arguments import GUIDES, ParameterGuide
from api.application.agent.tool_schema import ToolSchema

MAX_ECHOED_INPUT = 80
LIST_SEPARATOR = ", "
PATH_SEPARATOR = "."
MISSING = "missing"
UNKNOWN_PARAMETER = "extra_forbidden"


class ToolTeaching:
    def __init__(self, schema: ToolSchema) -> None:
        self._schema = schema

    def paragraph(self, error: ValidationError) -> str:
        sentences = {
            self._path(detail): self._sentence(detail)
            for detail in error.errors(include_url=False, include_context=False)
        }
        lines = " ".join(sentences.values())
        name = self._schema.name
        return f"A chamada de {name} não foi executada. {lines} Corrija e chame de novo."

    def _sentence(self, detail: ErrorDetails) -> str:
        path = self._path(detail)
        if detail["type"] == UNKNOWN_PARAMETER:
            return f"O parâmetro `{path}` não existe nesta tool. {self._accepted_parameters()}"
        guide = self._guide_of(detail)
        if detail["type"] == MISSING:
            opening = f"O parâmetro `{path}` é obrigatório e não veio."
        else:
            echoed = json.dumps(detail["input"], ensure_ascii=False, default=str)
            shown = echoed[:MAX_ECHOED_INPUT]
            opening = f"O parâmetro `{path}` veio como {shown}."
        return f"{opening} Aceita {guide.accepted}. Exemplo: {guide.example}."

    def _guide_of(self, detail: ErrorDetails) -> ParameterGuide:
        leaf = str(detail["loc"][-1])
        return self._schema.guides.get(leaf) or GUIDES[leaf]

    def _accepted_parameters(self) -> str:
        names = LIST_SEPARATOR.join(self._schema.guides)
        if names:
            return f"Os parâmetros aceitos são: {names}."
        return "Esta tool não recebe parâmetros; chame com {}."

    @staticmethod
    def _path(detail: ErrorDetails) -> str:
        return PATH_SEPARATOR.join(map(str, detail["loc"]))
