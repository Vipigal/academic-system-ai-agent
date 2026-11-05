import inspect
from collections.abc import Awaitable, Callable, Iterator
from dataclasses import dataclass
from types import FunctionType
from typing import Self, get_args, get_type_hints

from pydantic import BaseModel

from api.domain.ontology.catalog import ONTOLOGIES
from api.domain.ontology.model import Ontology

MAX_DESCRIPTION_LENGTH = 200
DECLARED_ONTOLOGIES = "declared_ontologies"
IDENTITY_TERMS = (
    "cpf",
    "customer",
    "email",
    "identity",
    "person",
    "session",
    "student",
    "tax",
    "user",
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
            if any(term in parameter.lower() for term in IDENTITY_TERMS):
                raise ToolContractError(f"{self.name} recebe identidade em {parameter}")

    @staticmethod
    def _parameter_names(function: FunctionType) -> Iterator[str]:
        hints = get_type_hints(function)
        for name in inspect.signature(function).parameters:
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
        return tuple(
            ToolDefinition.from_function(function)
            for name, function in inspect.getmembers(group_class, inspect.isfunction)
            if not name.startswith("_")
        )

    @classmethod
    def _bind(cls, group: object) -> Iterator[RegisteredTool]:
        for definition in cls.describe(type(group)):
            yield RegisteredTool(definition, getattr(group, definition.name))
