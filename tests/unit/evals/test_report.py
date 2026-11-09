from evals.golden.loader import GoldenSet
from evals.golden.problems import Problem
from evals.golden.query_checks import FactValue
from evals.golden.report import CheckReport
from tests.unit.evals.items_support import attack, question

GOLDEN = GoldenSet(
    (question(split="holdout"), question(id="FI-02")),
    (attack(split="holdout"), attack(id="AT-02"), attack(id="AT-03")),
)
FACT = FactValue("FI-01", "debt_total", "R$ 277,05", divergent=False)


def test_report_counts_by_area_kind_and_split_and_lists_each_fact() -> None:
    lines = list(CheckReport(GOLDEN, [FACT], []).lines())
    assert lines == [
        "Itens: 2 perguntas, 3 ataques",
        "Ações de protocolo: 0",
        "Escopo: 0",
        "Por área: AT 3, FI 2",
        "Por kind: answerable 2, attack 3",
        "Por split: dev 3, holdout 2",
        "Holdout por área: AT 1, FI 1",
        "Holdout por kind: answerable 1, attack 1",
        "Fatos: 1",
        "  FI-01 debt_total = R$ 277,05",
        "Problemas: 0",
        "OK",
    ]


def test_any_problem_fails_the_report() -> None:
    report = CheckReport(GOLDEN, [], [Problem("FI-01", "fato sem valor")])
    assert not report.passed
    assert list(report.lines())[-2:] == ["  FI-01: fato sem valor", "FALHOU"]
