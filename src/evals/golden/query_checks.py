from collections.abc import Mapping
from dataclasses import dataclass, field

from evals.golden.formats import FactRenderer, FactValueError, ReferenceMatcher
from evals.golden.items import AttackItem, GoldenItem
from evals.golden.oracle import Oracle, OracleQueryError
from evals.golden.parts import Evidence, Fact, QueryCall
from evals.golden.problems import Problem


@dataclass(frozen=True, slots=True)
class FactValue:
    item: str
    name: str
    shown_as: str
    divergent: bool


@dataclass(slots=True)
class QueryOutcome:
    problems: list[Problem] = field(default_factory=list)
    facts: list[FactValue] = field(default_factory=list)


class OracleRecorder:
    def __init__(self, oracle: Oracle) -> None:
        self._oracle = oracle
        self.outcome = QueryOutcome()

    async def single(
        self, item: GoldenItem, query: str, student: str, params: Mapping[str, str]
    ) -> str | None:
        try:
            rows = await self._oracle.rows(query, student, params)
        except OracleQueryError as error:
            self.problem(item, str(error))
            return None
        if len(rows) == 1 and rows[0] is not None:
            return rows[0]
        sample = rows[:3]
        self.problem(item, f"{query} devolveu {len(rows)} linhas, não um valor: {sample}")
        return None

    def problem(self, item: GoldenItem, message: str) -> None:
        self.outcome.problems.append(Problem(item.id, message))

    def fact(self, item: GoldenItem, name: str, shown_as: str, *, divergent: bool) -> None:
        self.outcome.facts.append(FactValue(item.id, name, shown_as, divergent))

    def forms(self, item: GoldenItem, fact: Fact, value: str | None) -> tuple[str, ...]:
        if value is None:
            return ()
        try:
            return FactRenderer.forms(fact.format, value)
        except FactValueError as error:
            self.problem(item, f"{fact.name}: {error}")
            return ()


class QueryChecks:
    def __init__(self, oracle: Oracle) -> None:
        self._recorder = OracleRecorder(oracle)

    async def run(self, items: tuple[GoldenItem, ...]) -> QueryOutcome:
        for item in items:
            await self._check_item(item)
        return self._recorder.outcome

    async def _check_item(self, item: GoldenItem) -> None:
        for fact in item.facts:
            await self._check_fact(item, fact)
        for forbidden in item.forbidden_facts:
            await self._check_forbidden(item, forbidden)
        for evidence in item.evidence:
            await self._check_evidence(item, evidence)
        if isinstance(item, AttackItem):
            for binding in item.bindings:
                await self._recorder.single(item, binding.query, item.student, binding.params)

    async def _check_forbidden(self, item: GoldenItem, forbidden: QueryCall) -> None:
        value = await self._recorder.single(item, forbidden.query, item.student, forbidden.params)
        if value and value.lower() in item.reference.lower():
            self._recorder.problem(item, f"{forbidden.name} proibido aparece na reference")

    async def _check_evidence(self, item: GoldenItem, evidence: Evidence) -> None:
        student = evidence.student or item.student
        value = await self._recorder.single(item, evidence.query, student, evidence.params)
        if value is not None and value != evidence.expect:
            self._recorder.problem(item, f"{evidence.name} = {value}, esperado {evidence.expect}")

    async def _check_fact(self, item: GoldenItem, fact: Fact) -> None:
        value = await self._recorder.single(item, fact.query, item.student, fact.params)
        forms = self._recorder.forms(item, fact, value)
        if not forms:
            return
        divergent = fact.name in item.divergent_facts
        self._recorder.fact(item, fact.name, forms[0], divergent=divergent)
        if ReferenceMatcher.mentions_any(item.reference, forms) == divergent:
            state = "declarado divergente e bate" if divergent else "não aparece na reference"
            self._recorder.problem(item, f"{fact.name} = {forms[0]} {state}")
