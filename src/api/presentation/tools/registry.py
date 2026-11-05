import inspect
from collections.abc import Awaitable, Callable, Iterator
from dataclasses import dataclass
from types import FunctionType
from typing import Self, get_args, get_origin, get_type_hints

from pydantic import BaseModel

from api.application.dto.tool_result import ToolResult
from api.domain.ontology.catalog import ONTOLOGIES
from api.domain.ontology.model import Ontology

MAX_DESCRIPTION_LENGTH = 200
DECLARED_ONTOLOGIES = "declared_ontologies"
ALLOWED_PARAMETERS = frozenset(
    {
        "term",
        "course",
        "modality",
        "unit",
        "area",
        "enrollment",
        "semester",
        "subject",
        "pending_only",
        "page",
        "offset",
        "limit",
        "status",
        "kind",
        "period",
        "year",
        "service",
        "number",
        "message",
        "query",
    }
)


class ToolContractError(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class ToolDefinition:
    name: str
    description: str
    ontologies: tuple[Ontology, ...]

    @classmethod
    def from_function(cls, function: FunctionType) -> Self:
        definition = cls(
            name=function.__name__,
            description=inspect.getdoc(function) or "",
            ontologies=getattr(function, DECLARED_ONTOLOGIES, ()),
        )
        definition._check_description()
        definition._check_ontologies()
        definition._check_async(function)
        definition._check_return(function)
        definition._check_parameters(function)
        return definition

    def _check_description(self) -> None:
        size = len(self.description)
        if not 0 < size <= MAX_DESCRIPTION_LENGTH:
            raise ToolContractError(
                f"A descrição de {self.name} tem {size} caracteres; "
                f"use a docstring, com até {MAX_DESCRIPTION_LENGTH}"
            )

    def _check_ontologies(self) -> None:
        if not self.ontologies:
            raise ToolContractError(f"{self.name} não declara nenhuma ontologia")
        for ontology in self.ontologies:
            if ontology not in ONTOLOGIES:
                raise ToolContractError(f"{self.name} declara {ontology.key}, fora do catálogo")

    def _check_parameters(self, function: FunctionType) -> None:
        for parameter in self._parameter_names(function):
            if parameter not in ALLOWED_PARAMETERS:
                raise ToolContractError(f"{self.name} recebe {parameter}, fora dos permitidos")

    def _check_async(self, function: FunctionType) -> None:
        if not inspect.iscoroutinefunction(function):
            raise ToolContractError(f"{self.name} precisa ser async")

    def _check_return(self, function: FunctionType) -> None:
        returned = get_type_hints(function).get("return")
        origin = get_origin(returned) or returned
        if not (isinstance(origin, type) and issubclass(origin, ToolResult)):
            raise ToolContractError(f"{self.name} precisa devolver ToolResult")

    @staticmethod
    def _parameter_names(function: FunctionType) -> Iterator[str]:
        hints = get_type_hints(function)
        for name in list(inspect.signature(function).parameters)[1:]:
            yield name
            annotation = hints.get(name)
            for hint in (annotation, *get_args(annotation)):
                if isinstance(hint, type) and issubclass(hint, BaseModel):
                    yield from hint.model_fields


@dataclass(frozen=True, slots=True)
class RegisteredTool:
    definition: ToolDefinition
    handler: Callable[..., Awaitable[BaseModel]]


class ToolRegistry:
    def __init__(self, *groups: object) -> None:
        self._tools = tuple(tool for group in groups for tool in self._bind(group))
        names = [tool.definition.name for tool in self._tools]
        for name in names:
            if names.count(name) > 1:
                raise ToolContractError(f"A tool {name} está registrada mais de uma vez")

    @property
    def tools(self) -> tuple[RegisteredTool, ...]:
        return self._tools

    @staticmethod
    def declares[F: Callable[..., object]](*ontologies: Ontology) -> Callable[[F], F]:
        def declare(function: F) -> F:
            setattr(function, DECLARED_ONTOLOGIES, ontologies)
            return function

        return declare

    @staticmethod
    def describe(group_class: type) -> tuple[ToolDefinition, ...]:
        public = [
            (name, inspect.getattr_static(group_class, name))
            for name in dir(group_class)
            if not name.startswith("_")
        ]
        for name, member in public:
            if not isinstance(member, FunctionType):
                raise ToolContractError(f"{group_class.__name__}.{name} não é método de instância")
        return tuple(ToolDefinition.from_function(member) for _, member in public)

    @classmethod
    def _bind(cls, group: object) -> Iterator[RegisteredTool]:
        for definition in cls.describe(type(group)):
            yield RegisteredTool(definition, getattr(group, definition.name))
