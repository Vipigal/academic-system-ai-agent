import math
from collections import defaultdict
from collections.abc import Iterator

from evals.golden.catalog import CatalogEntry
from evals.golden.items import GoldenItem, ProtocolActionItem, QuestionItem
from evals.golden.loader import GoldenSet
from evals.golden.oracle_names import QueryNames
from evals.golden.problems import Problem
from evals.golden.vocabulary import Kind, Split

MINIMUM_ATTACKS = 25
HOLDOUT_SHARE = 0.3
KIND_BY_AREA = {
    "SR": Kind.NO_DATA,
    "RE": Kind.REFUSAL,
    "AT": Kind.ATTACK,
    "ES": Kind.REFUSAL,
}
ACTION_AREAS = frozenset({"TR", "SV", "ES"})
ANCHOR_AREA = "TR"
SET_LEVEL = "golden"


class ActionChecks:
    @staticmethod
    def problems_of(action: ProtocolActionItem) -> Iterator[Problem]:
        if action.area not in ACTION_AREAS:
            yield Problem(action.id, f"prefixo {action.area} fora das ações de protocolo")
        if action.area == ANCHOR_AREA and not action.critical:
            yield Problem(action.id, "item de trancamento precisa ser crítico")
        if action.kind is Kind.ATTACK:
            yield Problem(action.id, "ataque pertence ao redteam.yaml")
        if not action.proposal.is_set:
            yield Problem(action.id, "ação de protocolo sem resultado esperado da proposta")


class StaticChecks:
    def __init__(self, catalog: dict[str, CatalogEntry], tools: frozenset[str]) -> None:
        self._catalog = catalog
        self._tools = tools

    def run(self, golden: GoldenSet) -> list[Problem]:
        problems = [*self._codes(golden), *self._split(golden.catalog_items)]
        if len(golden.attacks) < MINIMUM_ATTACKS:
            problems.append(Problem(SET_LEVEL, f"{len(golden.attacks)} ataques, mínimo 25"))
        for question in golden.questions:
            problems.extend(self._against_catalog(question))
        for action in golden.actions:
            problems.extend(ActionChecks.problems_of(action))
        for item in golden.items:
            problems.extend(self._item(item))
        return problems

    def _codes(self, golden: GoldenSet) -> Iterator[Problem]:
        ids = [item.id for item in golden.items]
        if len(ids) != len(set(ids)):
            yield Problem(SET_LEVEL, "ids repetidos")
        codes = {question.id for question in golden.questions}
        if codes != set(self._catalog):
            missing = sorted(set(self._catalog) - codes)
            extra = sorted(codes - set(self._catalog))
            yield Problem(SET_LEVEL, f"códigos fora do catálogo: faltam {missing}, sobram {extra}")

    def _against_catalog(self, question: QuestionItem) -> Iterator[Problem]:
        entry = self._catalog.get(question.id)
        if entry is None:
            return
        if question.question != entry.question:
            yield Problem(question.id, "pergunta diferente do catálogo")
        if question.reference != entry.reference:
            yield Problem(question.id, "reference diferente da resposta ideal do catálogo")
        if entry.case is not None and question.student != entry.case:
            yield Problem(question.id, f"aluno {question.student}, o catálogo usa {entry.case}")
        if entry.case is None and question.student_choice is None:
            yield Problem(question.id, "sem caso no catálogo e sem a consulta que escolhe o aluno")

    def _item(self, item: GoldenItem) -> Iterator[Problem]:
        expected_kind = KIND_BY_AREA.get(item.area, Kind.ANSWERABLE)
        if item.kind is not expected_kind:
            yield Problem(item.id, f"kind {item.kind}, a área pede {expected_kind}")
        unknown = set(item.tools.expected) | set(item.tools.forbidden)
        for tool in sorted(unknown - self._tools):
            yield Problem(item.id, f"tool {tool} fora do registro")
        if set(item.tools.expected) & set(item.tools.forbidden):
            yield Problem(item.id, "tool esperada e proibida ao mesmo tempo")
        for text in item.forbidden_text:
            if text.lower() in item.reference.lower():
                yield Problem(item.id, f"texto proibido {text!r} aparece na reference")
        yield from QueryNames.problems_of(item)

    @classmethod
    def _split(cls, items: tuple[GoldenItem, ...]) -> Iterator[Problem]:
        by_area: dict[str, list[GoldenItem]] = defaultdict(list)
        for item in items:
            by_area[item.area].append(item)
        for area, members in sorted(by_area.items()):
            holdout = sum(1 for member in members if member.split is Split.HOLDOUT)
            if not cls._is_about_a_third(holdout, len(members)):
                yield Problem(area, f"{holdout} de {len(members)} em holdout, esperado ~30%")

    @staticmethod
    def _is_about_a_third(holdout: int, total: int) -> bool:
        share = total * HOLDOUT_SHARE
        within = math.floor(share) <= holdout <= math.ceil(share)
        return within and holdout > 0
