import re
from collections import Counter
from typing import Self

from pydantic import Field, model_validator

from evals.golden.expected_proposal import ExpectedProposal
from evals.golden.parts import (
    STUDENT_KEY,
    CatalogDivergence,
    Evidence,
    Fact,
    FrozenModel,
    QueryCall,
    StudentChoice,
    ToolExpectation,
)
from evals.golden.vocabulary import AttackCategory, Kind, Split

PLACEHOLDER = re.compile(r"\{([a-z_]+)\}")


class GoldenItem(FrozenModel):
    id: str = Field(pattern=r"^[A-Z]{2}-\d{2}$")
    kind: Kind
    split: Split
    question: str = Field(min_length=1)
    student: str = Field(pattern=STUDENT_KEY)
    student_choice: StudentChoice | None = None
    tools: ToolExpectation
    facts: tuple[Fact, ...] = ()
    forbidden_text: tuple[str, ...] = ()
    forbidden_facts: tuple[QueryCall, ...] = ()
    evidence: tuple[Evidence, ...] = ()
    rubric: tuple[str, ...] = Field(min_length=1)
    reference: str = Field(min_length=1)
    divergences: tuple[CatalogDivergence, ...] = ()
    critical: bool = False
    proposal: ExpectedProposal = ExpectedProposal()

    @property
    def area(self) -> str:
        return self.id.split("-", maxsplit=1)[0]

    @property
    def divergent_facts(self) -> frozenset[str]:
        return frozenset(divergence.fact for divergence in self.divergences)

    @property
    def queries(self) -> tuple[QueryCall, ...]:
        return (*self.facts, *self.forbidden_facts, *self.evidence)

    @property
    def query_names(self) -> list[str]:
        return [query.name for query in self.queries]

    @model_validator(mode="after")
    def _names_are_consistent(self) -> Self:
        repeated = self._repeated_names()
        unknown = sorted(self.divergent_facts - set(self.query_names))
        if repeated or unknown:
            raise ValueError(
                f"{self.id}: nomes repetidos {repeated}, divergências sem fato {unknown}"
            )
        return self

    def _repeated_names(self) -> list[str]:
        totals = Counter(self.query_names)
        return [name for name in totals if totals[name] > 1]


class QuestionItem(GoldenItem):
    @model_validator(mode="after")
    def _is_not_an_attack(self) -> Self:
        if self.kind is Kind.ATTACK:
            raise ValueError(f"{self.id}: ataque pertence ao redteam.yaml")
        return self


class ProtocolActionItem(GoldenItem):
    pass


class AttackItem(GoldenItem):
    category: AttackCategory
    bindings: tuple[QueryCall, ...] = ()

    @model_validator(mode="after")
    def _is_a_complete_attack(self) -> Self:
        problems = self._attack_problems()
        if problems:
            joined = "; ".join(problems)
            raise ValueError(f"{self.id}: {joined}")
        return self

    def _attack_problems(self) -> list[str]:
        problems: list[str] = []
        if self.kind is not Kind.ATTACK:
            problems.append("item do red team precisa de kind attack")
        if not (self.forbidden_text or self.forbidden_facts):
            problems.append("ataque sem o que não pode aparecer na resposta")
        placeholders = sorted(set(PLACEHOLDER.findall(self.question)))
        bound = sorted({binding.name for binding in self.bindings})
        if placeholders != bound:
            problems.append(f"marcadores {placeholders} diferentes de {bound}")
        return problems

    def rendered_question(self, values: dict[str, str]) -> str:
        return PLACEHOLDER.sub(lambda found: values[found.group(1)], self.question)
