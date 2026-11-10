import inspect
from collections.abc import Awaitable, Callable, Iterator
from dataclasses import dataclass
from types import FunctionType
from typing import Self, get_origin, get_type_hints

from pydantic import BaseModel

from api.application.shared.tool_result import ToolResult

MAX_DESCRIPTION_LENGTH = 200


class ToolContractError(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class ToolDefinition:
    name: str
    description: str

    @classmethod
    def from_function(cls, function: FunctionType) -> Self:
        definition = cls(
            name=function.__name__,
            description=inspect.getdoc(function) or "",
        )
        definition._check_description()
        definition._check_async(function)
        definition._check_return(function)
        return definition

    def _check_description(self) -> None:
        size = len(self.description)
        if not 0 < size <= MAX_DESCRIPTION_LENGTH:
            raise ToolContractError(
                f"A descrição de {self.name} tem {size} caracteres; "
                f"use a docstring, com até {MAX_DESCRIPTION_LENGTH}"
            )

    def _check_async(self, function: FunctionType) -> None:
        if not inspect.iscoroutinefunction(function):
            raise ToolContractError(f"{self.name} precisa ser async")

    def _check_return(self, function: FunctionType) -> None:
        returned = get_type_hints(function).get("return")
        origin = get_origin(returned) or returned
        if not (isinstance(origin, type) and issubclass(origin, ToolResult)):
            raise ToolContractError(f"{self.name} precisa devolver ToolResult")


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
