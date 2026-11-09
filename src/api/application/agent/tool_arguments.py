import inspect
from collections.abc import Callable, Iterator, Sequence
from enum import Enum
from functools import cache
from types import MethodType
from typing import Annotated, get_args, get_type_hints

from pydantic import BaseModel, ConfigDict, Field, create_model
from pydantic.fields import FieldInfo

from api.application.agent.tools.registry import ToolContractError
from api.application.shared.page import DEFAULT_LIMIT, MAX_LIMIT, PageRequest
from api.application.shared.tool_parameters import Teaching

MIN_LIMIT = 1
MIN_OFFSET = 0
LIST_SEPARATOR = ", "
PATH_SEPARATOR = "."


class BoundedPage(PageRequest):
    model_config = ConfigDict(extra="forbid")

    offset: Annotated[
        int,
        Field(ge=MIN_OFFSET),
        Teaching(f"um inteiro a partir de {MIN_OFFSET}", str(MIN_OFFSET)),
    ] = MIN_OFFSET
    limit: Annotated[
        int,
        Field(ge=MIN_LIMIT, le=MAX_LIMIT),
        Teaching(f"um inteiro de {MIN_LIMIT} a {MAX_LIMIT}", str(DEFAULT_LIMIT)),
    ] = DEFAULT_LIMIT


PageArgument = Annotated[
    BoundedPage, Teaching("um objeto com offset e limit", '{"offset": 0, "limit": 20}')
]


class ToolArguments:
    @staticmethod
    def model_of(handler: Callable[..., object]) -> type[BaseModel]:
        function = handler.__func__ if isinstance(handler, MethodType) else handler
        return ToolArguments._inferred(function)

    @staticmethod
    @cache
    def _inferred(function: Callable[..., object]) -> type[BaseModel]:
        fields = get_type_hints(function, include_extras=True)
        fields.pop("return", None)
        for parameter in inspect.signature(function).parameters.values():
            hint = fields.get(parameter.name)
            if hint is None:
                continue
            kind = PageArgument if hint is PageRequest else hint
            required = parameter.default is inspect.Parameter.empty
            fields[parameter.name] = (kind, ... if required else parameter.default)
        return create_model(
            f"{function.__name__}_arguments", __config__=ConfigDict(extra="forbid"), **fields
        )

    @staticmethod
    @cache
    def json_schema_of(arguments: type[BaseModel]) -> dict[str, object]:
        return arguments.model_json_schema()

    @staticmethod
    def teaching_at(arguments: type[BaseModel], path: Sequence[str | int]) -> Teaching:
        field = arguments.model_fields[str(path[0])]
        for key in path[1:]:
            field = ToolArguments._nested_model(field, path).model_fields[str(key)]
        for found in (*field.metadata, *ToolArguments._flattened(field.annotation)):
            if isinstance(found, Teaching):
                return found
            if isinstance(found, type) and issubclass(found, Enum):
                return ToolArguments._of_enum(found)
        raise ToolContractError(
            f"O parâmetro {PATH_SEPARATOR.join(map(str, path))} não tem texto de ensino"
        )

    @staticmethod
    def _nested_model(field: FieldInfo, path: Sequence[str | int]) -> type[BaseModel]:
        for found in ToolArguments._flattened(field.annotation):
            if isinstance(found, type) and issubclass(found, BaseModel):
                return found
        raise ToolContractError(
            f"O parâmetro {PATH_SEPARATOR.join(map(str, path))} não é um objeto"
        )

    @staticmethod
    def _flattened(hint: object) -> Iterator[object]:
        yield hint
        for argument in get_args(hint):
            yield from ToolArguments._flattened(argument)

    @staticmethod
    def _of_enum(enum_type: type[Enum]) -> Teaching:
        values = [str(member.value) for member in enum_type]
        return Teaching(f"um destes valores: {LIST_SEPARATOR.join(values)}", values[0])
