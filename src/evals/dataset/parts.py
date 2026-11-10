from pydantic import BaseModel, ConfigDict

STUDENT_KEY = r"^Uni[A-Za-z]+(_EAD)?:\d{6}$"


class FrozenModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class ToolExpectation(FrozenModel):
    expected: tuple[str, ...]
    forbidden: tuple[str, ...]
