import inspect
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from types import MethodType
from typing import get_type_hints

from pydantic import BaseModel, ConfigDict, Field, create_model

from api.application.agent.tool_arguments import BoundedPage, ParameterGuide
from api.application.shared.page import PageRequest


@dataclass(frozen=True, slots=True)
class ToolSchema:
    name: str
    arguments: type[BaseModel]
    json_schema: Mapping[str, object]
    guides: Mapping[str, ParameterGuide]

    @staticmethod
    def of(handler: Callable[..., object]) -> ToolSchema:
        function = handler.__func__ if isinstance(handler, MethodType) else handler
        cached = SCHEMAS.get(function)
        if cached is None:
            cached = ToolSchema._infer(function)
            SCHEMAS[function] = cached
        return cached

    def validated(self, arguments: Mapping[str, object]) -> dict[str, object]:
        parsed = self.arguments.model_validate(arguments)
        return {name: getattr(parsed, name) for name in parsed.model_fields_set}

    @staticmethod
    def _infer(function: Callable[..., object]) -> ToolSchema:
        definitions = get_type_hints(function)
        definitions.pop("return", None)
        guides: dict[str, ParameterGuide] = {}
        for parameter in list(inspect.signature(function).parameters.values())[1:]:
            hint = definitions[parameter.name]
            guides[parameter.name] = ParameterGuide.of_parameter(parameter.name, hint)
            definitions[parameter.name] = ToolSchema._definition_of(
                parameter, hint, guides[parameter.name]
            )
        arguments = create_model(
            f"{function.__name__}_arguments", __config__=ConfigDict(extra="forbid"), **definitions
        )
        return ToolSchema(function.__name__, arguments, arguments.model_json_schema(), guides)

    @staticmethod
    def _definition_of(
        parameter: inspect.Parameter, hint: object, guide: ParameterGuide
    ) -> tuple[object, object]:
        kind = BoundedPage if hint is PageRequest else hint
        if parameter.default is inspect.Parameter.empty:
            return kind, Field(pattern=guide.pattern)
        return kind, Field(default=parameter.default, pattern=guide.pattern)


SCHEMAS: dict[Callable[..., object], ToolSchema] = {}
