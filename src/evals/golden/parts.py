from pydantic import BaseModel, ConfigDict, Field

from evals.golden.vocabulary import FactFormat

STUDENT_KEY = r"^Uni[A-Za-z]+(_EAD)?:\d{6}$"
SNAKE_NAME = r"^[a-z0-9_]+$"


class FrozenModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class QueryCall(FrozenModel):
    name: str = Field(pattern=SNAKE_NAME)
    query: str
    params: dict[str, str] = Field(default_factory=dict)


class Fact(QueryCall):
    format: FactFormat


class Evidence(QueryCall):
    expect: str
    student: str | None = Field(default=None, pattern=STUDENT_KEY)


class ToolExpectation(FrozenModel):
    expected: tuple[str, ...]
    forbidden: tuple[str, ...]


class CatalogDivergence(FrozenModel):
    fact: str
    catalog: str = Field(min_length=1)
    cause: str = Field(min_length=1)
