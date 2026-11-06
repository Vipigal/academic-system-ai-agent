from decimal import Decimal
from pathlib import Path

from api.application.agent.events import AgentEvent, StopReason
from evals.critical_consistency import CriticalConsistency
from evals.critical_rule import CriticalRule, RoundState
from evals.graders.verdict import GraderName
from tests.unit.evals import agent_script
from tests.unit.evals import run_support as support
from tests.unit.evals.items_support import question

TR_ITEM = question(
    id="TR-01",
    critical=True,
    proposal="none",
    question="Tranca a disciplina",
    tools={"expected": [], "forbidden": []},
    facts=[],
)
SV_ITEM = question(
    id="SV-01",
    proposal="ACA-010",
    question="Tranca o curso",
    tools={"expected": ["propose_protocol"], "forbidden": []},
    facts=[],
)
PLAIN_ITEM = question(id="FI-02", question="Quanto devo?", facts=[])
REFUSAL = agent_script.answer_events("Não existe trancamento de disciplina.")


def report_opening(directory: Path) -> str:
    return (directory / "report.md").read_text(encoding="utf-8").splitlines()[2]


async def test_a_full_report_comes_from_a_scripted_model(tmp_path: Path) -> None:
    def script(asked: str) -> tuple[AgentEvent, ...]:
        if asked == SV_ITEM.question:
            return agent_script.proposal_events("ACA-010")
        return agent_script.answer_events("Não existe trancamento de disciplina.")

    data = await support.run_items(
        tmp_path, agent_script.ScriptedDriver(script), [(TR_ITEM, 3), (SV_ITEM, 1), (PLAIN_ITEM, 1)]
    )
    report = (tmp_path / "report.md").read_text(encoding="utf-8")

    assert len(data.records) == 5
    for title in (
        "Rodada",
        "## Configuração",
        "gpt-6-luna",
        "student_agent_v1",
        "pass@1 médio",
        "Estabilidade entre repetições",
        "p50",
        "p95",
        "## Acerto por grader",
        "## Acerto por área",
        "## Acerto por kind",
        "Custo",
        "pass^3",
        "medida de consistência",
        "não prova ausência de bug",
    ):
        assert title in report


async def test_each_execution_is_recorded_as_soon_as_it_ends(tmp_path: Path) -> None:
    def script(asked: str) -> tuple[AgentEvent, ...]:
        lines = (tmp_path / "executions.jsonl").read_text().splitlines()
        assert asked == TR_ITEM.question
        assert len(lines) <= 3
        return agent_script.answer_events("Não.")

    (tmp_path / "executions.jsonl").touch()
    await support.run_items(tmp_path, agent_script.ScriptedDriver(script), [(TR_ITEM, 3)])

    assert len((tmp_path / "executions.jsonl").read_text().splitlines()) == 3


async def test_client_only_stays_out_of_the_files_and_only_the_verdict_remains(
    tmp_path: Path,
) -> None:
    driver = agent_script.ScriptedDriver(lambda _: agent_script.proposal_events("ACA-010"))
    data = await support.run_items(tmp_path, driver, [(SV_ITEM, 1)])

    for name in ("executions.jsonl", "judge_requests.jsonl", "report.md"):
        content = (tmp_path / name).read_text(encoding="utf-8")
        assert agent_script.SIGNED_VALUE not in content
        assert "client_only" not in content
    step = support.record_of(data, "SV-01#1").steps[0]
    assert step.guardrail_problems == ("proposta sem o bloco de confirmação do servidor",)


async def test_the_critical_rule_fails_the_round_and_opens_the_report(tmp_path: Path) -> None:
    answers = iter((REFUSAL, agent_script.proposal_events("ACA-010"), REFUSAL))
    driver = agent_script.ScriptedDriver(lambda _: next(answers))
    data = await support.run_items(tmp_path, driver, [(TR_ITEM, 3)])

    failures = CriticalRule.failures(data.records)
    assert [failure.grader for failure in failures] == [GraderName.PROPOSAL]
    lines = (tmp_path / "report.md").read_text(encoding="utf-8").splitlines()
    assert lines[2].startswith("**Rodada REPROVADA pela regra crítica:** 1 falhas")


async def test_a_round_without_critical_failure_passes(tmp_path: Path) -> None:
    driver = agent_script.ScriptedDriver(lambda _: agent_script.answer_events("Não existe."))
    data = await support.run_items(tmp_path, driver, [(TR_ITEM, 2)])

    assert CriticalRule.failures(data.records) == ()
    assert report_opening(tmp_path).startswith("**Rodada APROVADA pela regra crítica:**")


async def test_a_failure_outside_the_critical_items_does_not_fail_the_round(tmp_path: Path) -> None:
    driver = agent_script.ScriptedDriver(lambda _: agent_script.answer_events("Não sei."))
    data = await support.run_items(tmp_path, driver, [(SV_ITEM, 1)])

    assert CriticalRule.failures(data.records) == ()
    assert not data.records[0].passed


async def test_an_execution_stopped_by_the_model_limit_is_an_error_and_fails_the_round(
    tmp_path: Path,
) -> None:
    driver = agent_script.ScriptedDriver(
        lambda _: agent_script.answer_events("Não existe.", StopReason.MODEL_CALL_LIMIT)
    )
    data = await support.run_items(tmp_path, driver, [(TR_ITEM, 1)])

    assert data.records[0].error == "model_call_limit"
    assert CriticalRule.result(data.manifest, data.records).state is RoundState.FAILED
    report = (tmp_path / "report.md").read_text(encoding="utf-8")
    assert "| Execuções com erro | 1 |" in report
    assert not (tmp_path / "judge_requests.jsonl").exists()


async def test_a_round_without_the_critical_items_of_the_golden_is_incomplete(
    tmp_path: Path,
) -> None:
    driver = agent_script.ScriptedDriver(lambda _: agent_script.proposal_events("ACA-010"))
    data = await support.run_items(
        tmp_path, driver, [(PLAIN_ITEM, 1)], golden_critical=("TR-01", "PR-08")
    )

    result = CriticalRule.result(data.manifest, data.records)
    assert result.state is RoundState.INCOMPLETE
    assert result.exit_code == 2
    assert result.unplanned_critical_items == ("TR-01", "PR-08")
    assert report_opening(tmp_path).startswith("**Rodada INCOMPLETA pela regra crítica:**")


async def test_a_planned_execution_that_did_not_run_keeps_the_round_incomplete(
    tmp_path: Path,
) -> None:
    driver = agent_script.ScriptedDriver(lambda _: REFUSAL)
    data = await support.run_items(tmp_path, driver, [(TR_ITEM, 1)], extra_planned=("TR-01#2",))

    result = CriticalRule.result(data.manifest, data.records)
    assert result.state is RoundState.INCOMPLETE
    assert result.missing_executions == ("TR-01#2",)


async def test_a_critical_error_redone_on_resume_is_named_in_the_opening(tmp_path: Path) -> None:
    answers = iter((None, REFUSAL))
    driver = agent_script.ScriptedDriver(lambda _: next(answers))
    await support.run_items(tmp_path, driver, [(TR_ITEM, 1)])
    data = await support.run_items(tmp_path, driver, [(TR_ITEM, 1)])

    assert data.redone_critical == ("TR-01#1",)
    assert CriticalRule.result(data.manifest, data.records).state is RoundState.APPROVED
    opening = (tmp_path / "report.md").read_text(encoding="utf-8").split("## Configuração")[0]
    assert "Críticos refeitos na retomada: TR-01#1" in opening


async def test_pass_at_k_counts_only_the_critical_graders_in_every_repetition(
    tmp_path: Path,
) -> None:
    answers = iter((REFUSAL, agent_script.proposal_events("ACA-010"), REFUSAL))
    driver = agent_script.ScriptedDriver(lambda _: next(answers))
    data = await support.run_items(tmp_path, driver, [(TR_ITEM, 3)])

    summary = CriticalConsistency.of(data.manifest, data.records)
    assert summary.label == "pass^3"
    assert (summary.passing_items, summary.attempts_approved, summary.attempts_planned) == (0, 2, 3)
    assert summary.items[0].approved == 2


async def test_the_trace_id_of_the_execution_goes_to_the_jsonl_and_is_null_without_keys(
    tmp_path: Path,
) -> None:
    traced = agent_script.ScriptedDriver(lambda _: REFUSAL, trace_id="abc123")
    data = await support.run_items(tmp_path / "with", traced, [(TR_ITEM, 1)])
    untraced = agent_script.ScriptedDriver(lambda _: REFUSAL)
    bare = await support.run_items(tmp_path / "without", untraced, [(TR_ITEM, 1)])

    assert data.records[0].trace_id == "abc123"
    assert bare.records[0].trace_id is None


async def test_a_timeout_is_recorded_and_fails_a_critical_item_without_stopping_the_run(
    tmp_path: Path,
) -> None:
    def script(asked: str) -> tuple[AgentEvent, ...] | None:
        return None if asked == TR_ITEM.question else agent_script.answer_events("Ok.")

    data = await support.run_items(
        tmp_path, agent_script.ScriptedDriver(script), [(TR_ITEM, 1), (PLAIN_ITEM, 1)]
    )

    assert support.record_of(data, "TR-01#1").error == "AgentTimeoutError"
    assert support.record_of(data, "FI-02#1").error is None
    assert CriticalRule.failures(data.records)
    assert "TR-01#1" not in (tmp_path / "judge_requests.jsonl").read_text(encoding="utf-8")


async def test_a_record_carries_versions_timing_tokens_and_cost(tmp_path: Path) -> None:
    driver = agent_script.ScriptedDriver(lambda _: agent_script.proposal_events("ACA-010"))
    data = await support.run_items(tmp_path, driver, [(SV_ITEM, 1)])

    record = data.records[0]
    assert record.versions == support.VERSIONS
    assert record.total_ms >= (record.first_token_ms or 0) > 0
    assert (record.tokens_in, record.tokens_out, record.cost_usd) == (1000, 200, Decimal("0.0002"))
    assert record.steps[0].arguments == {"service": "ACA-010", "message": "Pedido"}


async def test_the_judge_requests_never_name_the_evaluated_model(tmp_path: Path) -> None:
    driver = agent_script.ScriptedDriver(lambda _: agent_script.answer_events("Resposta"))
    await support.run_items(tmp_path, driver, [(SV_ITEM, 1)])

    content = (tmp_path / "judge_requests.jsonl").read_text(encoding="utf-8")
    assert '"id":"SV-01#1"' in content
    assert support.VERSIONS.model not in content
    assert "fingerprint" not in content
