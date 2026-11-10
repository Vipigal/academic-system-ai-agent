from typing import Self

from pydantic import Field, PositiveInt, model_validator

from evals.dataset.expected_proposal import ExpectedProposal
from evals.dataset.parts import STUDENT_KEY, FrozenModel, ToolExpectation
from evals.dataset.vocabulary import AttackCategory, Kind, Split


class DatasetItem(FrozenModel):
    id: str = Field(pattern=r"^[A-Z]{2}-\d{2}$")
    kind: Kind
    split: Split
    question: str = Field(min_length=1)
    student: str = Field(pattern=STUDENT_KEY)
    tools: ToolExpectation
    forbidden_text: tuple[str, ...] = ()
    forbidden_values: tuple[str, ...] = ()
    rubric: tuple[str, ...] = Field(min_length=1)
    reference: str = Field(min_length=1)
    pass_k: PositiveInt | None = None
    proposal: ExpectedProposal = ExpectedProposal()
    history: tuple[str, ...] = ()

    @property
    def area(self) -> str:
        return self.id.split("-", maxsplit=1)[0]

    @property
    def gated(self) -> bool:
        return self.pass_k is not None


class QuestionItem(DatasetItem):
    @model_validator(mode="after")
    def _is_not_an_attack(self) -> Self:
        if self.kind is Kind.ATTACK:
            raise ValueError(f"{self.id}: ataque pertence ao security.yaml")
        return self


class ProtocolActionItem(DatasetItem):
    pass


class ScopeItem(DatasetItem):
    pass


class AttackItem(DatasetItem):
    category: AttackCategory

    @model_validator(mode="after")
    def _is_an_attack(self) -> Self:
        if self.kind is not Kind.ATTACK:
            raise ValueError(f"{self.id}: item de security precisa de kind attack")
        return self
