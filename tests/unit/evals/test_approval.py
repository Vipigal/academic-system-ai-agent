from evals.gate import GateFailure, RoundResult
from evals.graders.verdict import GraderName
from evals.report.approval import Approval, RoundApproval
from evals.report.metrics import Accuracy

CLEAN = RoundResult(failures=(), missing_executions=(), unplanned_gated_items=())
UNGATED = RoundResult((), (), ("TR-01",), gated_planned=False)
GOOD = Accuracy("graders", 90, 100)
LOW = Accuracy("juiz", 80, 100)
FAILURE = GateFailure("PR-08#5", GraderName.TRAJECTORY, ("faltou a tool",))


def test_a_round_without_gate_failures_and_both_rates_from_85_percent_is_approved() -> None:
    assert RoundApproval.of(CLEAN, GOOD, GOOD) == RoundApproval(Approval.APPROVED, ())
    assert RoundApproval.of(UNGATED, GOOD, Accuracy("juiz", 85, 100)).state is Approval.APPROVED


def test_a_gate_failure_fails_the_round_even_with_high_rates() -> None:
    failed = RoundResult((FAILURE, FAILURE), (), ())
    assert RoundApproval.of(failed, GOOD, GOOD).reasons == ("1 execução de gate falhou",)


def test_each_rate_below_85_percent_is_a_reason() -> None:
    approval = RoundApproval.of(CLEAN, LOW, LOW)
    assert approval.state is Approval.FAILED
    assert approval.reasons == ("graders abaixo de 85%", "juiz abaixo de 85%")


def test_a_round_the_judge_has_not_seen_is_pending() -> None:
    assert RoundApproval.of(CLEAN, GOOD, Accuracy("juiz", 0, 0)).state is Approval.PENDING
