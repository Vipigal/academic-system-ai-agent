from collections.abc import Mapping, Sequence
from datetime import date
from decimal import Decimal
from enum import StrEnum
from typing import Self

from pydantic import BaseModel, ConfigDict, Field

from api.application.page import Page, PageInfo
from api.domain.ontology.model import Ontology

MAX_CANDIDATES = 40


class ToolStatus(StrEnum):
    OK = "ok"
    EMPTY = "empty"
    NOT_FOUND = "not_found"
    AMBIGUOUS = "ambiguous"
    REFUSED = "refused"


class DataState(StrEnum):
    RECORDED = "recorded"
    NOT_YET = "not_yet"
    NOT_RECORDED = "not_recorded"


class StatedValue[T](BaseModel):
    model_config = ConfigDict(frozen=True)

    state: DataState
    value: T | None = Field(default=None, exclude_if=lambda value: value is None)

    @classmethod
    def recorded(cls, value: T) -> Self:
        return cls(state=DataState.RECORDED, value=value)

    @classmethod
    def not_yet(cls) -> Self:
        return cls(state=DataState.NOT_YET)

    @classmethod
    def not_recorded(cls) -> Self:
        return cls(state=DataState.NOT_RECORDED)


class Caveat(BaseModel):
    model_config = ConfigDict(frozen=True)

    ontology: str
    text: str

    @classmethod
    def from_ontology(cls, ontology: Ontology) -> Self:
        if ontology.caveat is None:
            raise ValueError(f"A ontologia {ontology.key} não tem aviso")
        return cls(ontology=ontology.key, text=ontology.caveat)


class Coverage(BaseModel):
    model_config = ConfigDict(frozen=True, serialize_by_alias=True)

    from_date: date = Field(serialization_alias="from")
    note: str


class Candidate(BaseModel):
    model_config = ConfigDict(frozen=True)

    code: str
    name: str


class ToolResult[T](BaseModel):
    model_config = ConfigDict(frozen=True)

    status: ToolStatus
    data: T | None = None
    page: PageInfo | None = Field(default=None, exclude_if=lambda page: page is None)
    totals: Mapping[str, Decimal | int] = Field(default_factory=dict)
    caveats: tuple[Caveat, ...] = ()
    coverage: Coverage | None = Field(default=None, exclude_if=lambda coverage: coverage is None)
    candidates: tuple[Candidate, ...] = ()

    @classmethod
    def ok(
        cls,
        data: T,
        *,
        totals: Mapping[str, Decimal | int] | None = None,
        caveats: tuple[Caveat, ...] = (),
        coverage: Coverage | None = None,
    ) -> Self:
        return cls(
            status=ToolStatus.OK,
            data=data,
            totals=totals or {},
            caveats=caveats,
            coverage=coverage,
        )

    @staticmethod
    def listing[I](
        page: Page[I],
        *,
        totals: Mapping[str, Decimal | int] | None = None,
        caveats: tuple[Caveat, ...] = (),
        coverage: Coverage | None = None,
    ) -> ToolResult[list[I]]:
        return ToolResult(
            status=ToolStatus.OK if page.info.total else ToolStatus.EMPTY,
            data=list(page.items),
            page=page.info,
            totals=totals or {},
            caveats=caveats,
            coverage=coverage,
        )

    @staticmethod
    def items[I](
        values: Sequence[I],
        *,
        totals: Mapping[str, Decimal | int] | None = None,
        caveats: tuple[Caveat, ...] = (),
        coverage: Coverage | None = None,
    ) -> ToolResult[list[I]]:
        return ToolResult(
            status=ToolStatus.OK if values else ToolStatus.EMPTY,
            data=list(values),
            totals=totals or {},
            caveats=caveats,
            coverage=coverage,
        )

    @classmethod
    def not_found(cls, candidates: tuple[Candidate, ...]) -> Self:
        return cls(status=ToolStatus.NOT_FOUND, candidates=candidates[:MAX_CANDIDATES])

    @classmethod
    def ambiguous(cls, candidates: tuple[Candidate, ...]) -> Self:
        return cls(status=ToolStatus.AMBIGUOUS, candidates=candidates[:MAX_CANDIDATES])

    @classmethod
    def refused(cls, data: T | None = None, *, caveats: tuple[Caveat, ...] = ()) -> Self:
        return cls(status=ToolStatus.REFUSED, data=data, caveats=caveats)
