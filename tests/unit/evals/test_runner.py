from decimal import Decimal
from pathlib import Path

from api.application.agent.events import AgentEvent, StopReason
from evals.gate import GateRule, RoundState
from evals.graders.verdict import GraderName
from evals.report.metrics import Consistency
from evals.report.summary import RunSummary
from evals.run_data import RunData
from tests.unit.evals import agent_script
from tests.unit.evals import run_support as support
from tests.unit.evals.items_support import question

TR_ITEM = question(
    id="TR-01",
    pass_k=5,
    proposal="none",
    question="Tranca a disciplina",
    tools={"expected": [], "forbidden": []},
)
SV_ITEM = question(
    id="SV-01",
    proposal="ACA-010",
    question="Tranca o curso",
    tools={"expected": ["propose_protocol"], "forbidden": []},
)
PLAIN_ITEM = question(id="FI-02", question="Quanto devo?")
REFUSAL = agent_script.answer_events("Não existe trancamento de disciplina.")


def summary_opening(data: RunData) -> str:
    return RunSummary.render(data).splitlines()[0]


async def test_a_full_report_comes_from_a_scripted_model(tmp_path: Path) -> None:
    def script(asked: str) -> tuple[AgentEvent, ...]:
        if asked == SV_ITEM.question:
            return agent_script.proposal_events("ACA-010")
        return agent_script.answer_events("Não existe trancamento de disciplina.")

    data = await support.run_items(
        tmp_path, agent_script.ScriptedDriver(script), [(TR_ITEM, 3), (SV_ITEM, 1), (PLAIN_ITEM, 1)]
    )
    summary = RunSummary.render(data)

    assert len(data.records) == 5
    for title in (
        "Rodada",
        "Graders: ",
        "n = 5",
        "Juiz: sem dados",
        "pass^3",
        "p50",
        "p95",
        "Custo",
    ):
        assert title in summary


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

    for name in ("executions.jsonl", "judge_requests.jsonl"):
        content = (tmp_path / name).read_text(encoding="utf-8")
        assert agent_script.SIGNED_VALUE not in content
        assert "client_only" not in content
    step = support.record_of(data, "SV-01#1").steps[0]
    assert step.guardrail_problems == ("proposta sem o bloco de confirmação do servidor",)


async def test_the_gate_fails_the_round_and_opens_the_summary(tmp_path: Path) -> None:
    answers = iter((REFUSAL, agent_script.proposal_events("ACA-010"), REFUSAL))
    driver = agent_script.ScriptedDriver(lambda _: next(answers))
    data = await support.run_items(tmp_path, driver, [(TR_ITEM, 3)])

    failures = GateRule.failures(data.records)
    assert [failure.grader for failure in failures] == [GraderName.PROPOSAL]
    assert summary_opening(data) == "Rodada REPROVADA: 1 falhas de gate"


async def test_a_round_without_critical_failure_passes(tmp_path: Path) -> None:
    driver = agent_script.ScriptedDriver(lambda _: agent_script.answer_events("Não existe."))
    data = await support.run_items(tmp_path, driver, [(TR_ITEM, 2)])

    assert GateRule.failures(data.records) == ()
    assert summary_opening(data) == "Rodada APROVADA: 0 falhas de gate"


async def test_a_failure_outside_the_critical_items_does_not_fail_the_round(tmp_path: Path) -> None:
    driver = agent_script.ScriptedDriver(lambda _: agent_script.answer_events("Não sei."))
    data = await support.run_items(tmp_path, driver, [(SV_ITEM, 1)])

    assert GateRule.failures(data.records) == ()
    assert not data.records[0].passed


async def test_an_execution_stopped_by_the_model_limit_is_an_error_and_fails_the_round(
    tmp_path: Path,
) -> None:
    driver = agent_script.ScriptedDriver(
        lambda _: agent_script.answer_events("Não existe.", StopReason.MODEL_CALL_LIMIT)
    )
    data = await support.run_items(tmp_path, driver, [(TR_ITEM, 1)])

    assert data.records[0].error == "model_call_limit"
    assert GateRule.result(data.manifest, data.records).state is RoundState.FAILED
    assert not (tmp_path / "judge_requests.jsonl").exists()


async def test_a_round_without_any_gated_item_has_no_gate(tmp_path: Path) -> None:
    driver = agent_script.ScriptedDriver(lambda _: agent_script.proposal_events("ACA-010"))
    data = await support.run_items(
        tmp_path, driver, [(PLAIN_ITEM, 1)], gated_items=("TR-01", "PR-08")
    )

    result = GateRule.result(data.manifest, data.records)
    assert result.state is RoundState.UNGATED
    assert result.exit_code == 0
    assert summary_opening(data) == "Rodada SEM GATE: 0 falhas de gate"


async def test_a_round_with_part_of_the_gated_items_is_partial(tmp_path: Path) -> None:
    driver = agent_script.ScriptedDriver(lambda _: REFUSAL)
    data = await support.run_items(tmp_path, driver, [(TR_ITEM, 2)], gated_items=("TR-01", "PR-08"))

    result = GateRule.result(data.manifest, data.records)
    assert result.state is RoundState.PARTIAL
    assert result.exit_code == 2
    assert result.unplanned_gated_items == ("PR-08",)


async def test_consistency_counts_every_repeated_item_on_every_grader(tmp_path: Path) -> None:
    answers = iter((REFUSAL, REFUSAL, agent_script.answer_events("Não sei."), REFUSAL))
    driver = agent_script.ScriptedDriver(lambda _: next(answers))
    data = await support.run_items(tmp_path, driver, [(TR_ITEM, 2), (PLAIN_ITEM, 2)])

    consistency = Consistency.of(data.records)
    assert (consistency.label, consistency.items) == ("pass^2", 2)


async def test_a_planned_execution_that_did_not_run_keeps_the_round_incomplete(
    tmp_path: Path,
) -> None:
    driver = agent_script.ScriptedDriver(lambda _: REFUSAL)
    data = await support.run_items(tmp_path, driver, [(TR_ITEM, 1)], extra_planned=("TR-01#2",))

    result = GateRule.result(data.manifest, data.records)
    assert result.state is RoundState.INCOMPLETE
    assert result.missing_executions == ("TR-01#2",)


async def test_a_gated_error_redone_on_resume_is_tracked(tmp_path: Path) -> None:
    answers = iter((None, REFUSAL))
    driver = agent_script.ScriptedDriver(lambda _: next(answers))
    await support.run_items(tmp_path, driver, [(TR_ITEM, 1)])
    data = await support.run_items(tmp_path, driver, [(TR_ITEM, 1)])

    assert len(data.records) == 1
    assert GateRule.result(data.manifest, data.records).state is RoundState.APPROVED


async def test_pass_at_k_counts_only_the_critical_graders_in_every_repetition(
    tmp_path: Path,
) -> None:
    answers = iter((REFUSAL, agent_script.proposal_events("ACA-010"), REFUSAL))
    driver = agent_script.ScriptedDriver(lambda _: next(answers))
    data = await support.run_items(tmp_path, driver, [(TR_ITEM, 3)])

    pass_k = GateRule.pass_k(data.manifest, data.records)
    assert (pass_k.label, pass_k.passing_items, pass_k.items) == ("pass^3", 0, 1)


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
    assert GateRule.failures(data.records)
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


async def test_the_judge_sees_what_the_tools_returned_but_never_the_client_only_part(
    tmp_path: Path,
) -> None:
    driver = agent_script.ScriptedDriver(lambda _: agent_script.proposal_events("ACA-010"))
    await support.run_items(tmp_path, driver, [(SV_ITEM, 1)])

    content = (tmp_path / "judge_requests.jsonl").read_text(encoding="utf-8")
    assert '"name":"propose_protocol"' in content
    assert '"data":{"service":{"code":"ACA-010"}' in content
    assert agent_script.SIGNED_VALUE not in content
