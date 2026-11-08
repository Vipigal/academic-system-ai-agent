import inspect
from collections.abc import Iterator, Mapping
from enum import Enum
from typing import Self, get_args, get_type_hints

from pydantic import BaseModel

from api.application.agent.tools.registry import RegisteredTool
from api.application.shared.page import PageRequest
from tests.integration.agent import invariant_queries as queries
from tests.integration.agent.invariant_json import Arguments, ToolCall
from tests.integration.support.owned import Owned
from tests.integration.support.sql_oracle import SqlOracle

type Identifiers = dict[str, tuple[str, ...]]
MISSING = {"enrollment": "UniSaoPaulo:999999", "subject": "ZZZ9999", "number": "20990000001"}
FIXED_VALUES: Mapping[str, tuple[object, ...]] = {
    "term": ("2026/2", "2022/1"),
    "course": ("Enfermagem", "Inexistente"),
    "semester": (3, 99),
    "year": (2026, 1999),
    "period": ("2026-10", "x"),
    "service": ("DOC-001", "ACA-021", "XYZ-999"),
    "message": ("Preciso de uma declaração de matrícula.",),
    "query": ("Semana 2",),
    "page": (PageRequest(offset=1, limit=3),),
}


def joined(identifiers: frozenset[str] | set[str]) -> str:
    return ",".join(sorted(identifiers))


def flattened(arguments: Arguments) -> Arguments:
    nested = {
        name: value
        for model in arguments.values()
        if isinstance(model, BaseModel)
        for name, value in model
        if name in model.model_fields_set
    }
    return {**arguments, **nested}


def enrollment_refs(owned: Owned) -> frozenset[str]:
    return frozenset(":".join(key) for key in owned.enrollment_keys)


class PersonArguments:
    def __init__(self, oracle: SqlOracle, owned: Owned) -> None:
        self._oracle = oracle
        self._owned = owned
        self._enrollments = joined(enrollment_refs(owned))
        self._brands = joined({brand for brand, _ in owned.enrollment_keys})

    async def own(self) -> Identifiers:
        subjects = await self._oracle.values(queries.OWN_SUBJECTS, enrollments=self._enrollments)
        return {
            "enrollment": tuple(sorted(enrollment_refs(self._owned))[:1]),
            "subject": tuple(sorted(subjects)[:1]),
            "number": tuple(sorted(self._owned.protocol_ids)[:1]),
        }

    async def foreign(self) -> Identifiers:
        protocols = joined(self._owned.protocol_ids)
        return {
            "enrollment": await self._of_others(queries.FOREIGN_ENROLLMENTS),
            "subject": await self._of_others(queries.FOREIGN_SUBJECTS),
            "number": tuple(
                sorted(await self._oracle.values(queries.FOREIGN_PROTOCOLS, protocols=protocols))
            ),
        }

    async def values(self, foreign: Identifiers) -> Mapping[str, tuple[object, ...]]:
        own = await self.own()
        units = (*sorted(await self._oracle.values(queries.FOREIGN_UNITS)), "Inexistente")
        identifiers = {
            name: (*own[name], *foreign[name], missing) for name, missing in MISSING.items()
        }
        return {**FIXED_VALUES, **identifiers, "unit": units}

    async def _of_others(self, sql: str) -> tuple[str, ...]:
        found = await self._oracle.values(sql, enrollments=self._enrollments, brands=self._brands)
        return tuple(sorted(found))


class ArgumentPool:
    def __init__(self, values: Mapping[str, tuple[object, ...]], foreign: Identifiers) -> None:
        self._values = values
        self.foreign = foreign

    @classmethod
    async def of(cls, oracle: SqlOracle, owned: Owned) -> Self:
        person = PersonArguments(oracle, owned)
        foreign = await person.foreign()
        return cls(await person.values(foreign), foreign)

    def calls(self, tool: RegisteredTool) -> Iterator[tuple[str | None, Arguments]]:
        hints = get_type_hints(tool.handler)
        base = self.base(tool)
        yield None, base
        for name in inspect.signature(tool.handler).parameters:
            for varied, value in self._variations(name, hints[name]):
                yield varied, {**base, name: value}

    def base(self, tool: RegisteredTool) -> Arguments:
        hints = get_type_hints(tool.handler)
        return {
            name: self._candidates(name, hints[name])[0]
            for name, parameter in inspect.signature(tool.handler).parameters.items()
            if parameter.default is inspect.Parameter.empty
        }

    def _variations(self, name: str, hint: object) -> Iterator[tuple[str, object]]:
        nested = self._nested(name, hint)
        if nested is None:
            yield from ((name, value) for value in self._candidates(name, hint))
            return
        for field, info in nested.model_fields.items():
            for value in self._candidates(field, info.annotation):
                yield field, nested.model_validate({field: value})

    def _nested(self, name: str, hint: object) -> type[BaseModel] | None:
        if name in self._values:
            return None
        for option in (hint, *get_args(hint)):
            if isinstance(option, type) and issubclass(option, BaseModel):
                return option
        return None

    def _candidates(self, name: str, hint: object) -> tuple[object, ...]:
        for option in (hint, *get_args(hint)):
            if isinstance(option, type) and issubclass(option, Enum):
                return tuple(option)
            if option is bool:
                return (True, False)
        return self._values[name]


class Sweep:
    @classmethod
    async def run(cls, tools: tuple[RegisteredTool, ...], pool: ArgumentPool) -> list[ToolCall]:
        return [
            await cls.call(tool, varied, arguments)
            for tool in tools
            for varied, arguments in pool.calls(tool)
        ]

    @staticmethod
    async def call(tool: RegisteredTool, varied: str | None, arguments: Arguments) -> ToolCall:
        result = await tool.handler(**arguments)
        output = result.model_dump(mode="json", by_alias=True)
        return ToolCall(tool.definition.name, varied, arguments, output)

    @staticmethod
    def parameters_of(tool: RegisteredTool) -> Iterator[str]:
        hints = get_type_hints(tool.handler)
        for name in inspect.signature(tool.handler).parameters:
            yield name
            for hint in (hints[name], *get_args(hints[name])):
                if isinstance(hint, type) and issubclass(hint, BaseModel):
                    yield from hint.model_fields
