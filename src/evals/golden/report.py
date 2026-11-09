from collections import Counter
from collections.abc import Iterator
from operator import attrgetter

from evals.golden.items import GoldenItem
from evals.golden.loader import GoldenSet
from evals.golden.problems import Problem
from evals.golden.query_checks import FactValue
from evals.golden.vocabulary import Split

SUMMARY_KEYS = (
    ("área", attrgetter("area")),
    ("kind", attrgetter("kind.value")),
    ("split", attrgetter("split.value")),
)
HOLDOUT_KEYS = SUMMARY_KEYS[:2]


class CheckReport:
    def __init__(self, golden: GoldenSet, facts: list[FactValue], problems: list[Problem]) -> None:
        self._golden = golden
        self._facts = facts
        self._problems = problems

    @property
    def passed(self) -> bool:
        return not self._problems

    def lines(self) -> Iterator[str]:
        yield from self._summary()
        yield f"Fatos: {len(self._facts)}"
        yield from (self._fact_line(fact) for fact in self._facts)
        yield f"Problemas: {len(self._problems)}"
        yield from (f"  {problem.render()}" for problem in self._problems)
        yield "OK" if self.passed else "FALHOU"

    def _summary(self) -> Iterator[str]:
        golden = self._golden
        yield f"Itens: {len(golden.questions)} perguntas, {len(golden.attacks)} ataques"
        yield f"Ações de protocolo: {len(golden.actions)}"
        holdout = tuple(item for item in golden.items if item.split is Split.HOLDOUT)
        for title, key in SUMMARY_KEYS:
            yield self._counts(f"Por {title}", golden.items, key)
        for title, key in HOLDOUT_KEYS:
            yield self._counts(f"Holdout por {title}", holdout, key)

    @staticmethod
    def _counts(title: str, members: tuple[GoldenItem, ...], key: attrgetter[str]) -> str:
        counts = Counter(key(item) for item in members)
        named = sorted(counts.items())
        parts = ", ".join(f"{name} {total}" for name, total in named)
        return f"{title}: {parts}"

    @staticmethod
    def _fact_line(fact: FactValue) -> str:
        mark = " (divergente do catálogo)" if fact.divergent else ""
        return f"  {fact.item} {fact.name} = {fact.shown_as}{mark}"
