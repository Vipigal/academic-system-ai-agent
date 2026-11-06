import re
from pathlib import Path

from evals.judge.verdicts import CriterionOutcome, CriterionVerdict, JudgedVerdict
from evals.page.payload import PagePayload
from evals.page.results_page import ResultsPage
from evals.page.review_sample import ReviewSample
from evals.report import RunReport
from evals.run_data import RunData
from evals.run_files import JsonLines, RunFiles
from tests.unit.evals import agent_script
from tests.unit.evals import run_support as support
from tests.unit.evals.items_support import question

HOSTILE = '</script><script>alert("x")</script> & ' + chr(0x2028) + " fim"
ITEM = question(
    id="TR-01",
    critical=True,
    proposal="ACA-010",
    question="Tranca o curso",
    tools={"expected": [], "forbidden": []},
    facts=[],
)
ITEM_IDS = [area + "-" + str(number).zfill(2) for area in ("FI", "PR") for number in range(1, 16)]
PASS = CriterionOutcome.APPROVED
FAIL = CriterionOutcome.REJECTED
UNKNOWN = CriterionOutcome.UNKNOWN
DATA_BLOCK = re.compile(r'<script type="application/json" id="run-data">(.*?)</script>', re.DOTALL)


def payload_of(page: str) -> PagePayload:
    found = DATA_BLOCK.search(page)
    assert found is not None
    return PagePayload.model_validate_json(found.group(1))


async def run_with_proposal(directory: Path, answer: str = "Preparei.") -> RunData:
    driver = agent_script.ScriptedDriver(lambda _: agent_script.proposal_events("ACA-010", answer))
    return await support.run_items(directory, driver, [(ITEM, 2)])


def judged_as(key: str, outcome: CriterionOutcome) -> JudgedVerdict:
    criterion = CriterionVerdict(criterion=1, reasoning="Raciocínio do juiz.", verdict=outcome)
    return JudgedVerdict(id=key, criteria=(criterion,), judge_model="claude-sonnet-5-5")


async def test_the_page_is_self_contained_and_written_with_the_report(tmp_path: Path) -> None:
    await run_with_proposal(tmp_path)
    page = (tmp_path / "report.html").read_text(encoding="utf-8")

    assert page.startswith("<!doctype html>")
    for external in ("https://", "http://", 'src="', "<link"):
        assert external not in page


async def test_the_page_opens_with_the_state_and_keeps_every_execution(tmp_path: Path) -> None:
    await run_with_proposal(tmp_path)
    payload = payload_of((tmp_path / "report.html").read_text(encoding="utf-8"))

    assert payload.state == "REPROVADA"
    assert payload.consistency_label == "pass^2"
    assert {execution.key for execution in payload.executions} == {"TR-01#1", "TR-01#2"}
    labels = {indicator.label for indicator in payload.indicators}
    assert {"pass^2", "pass@1 médio", "Rubrica", "Latência p95", "Custo", "Modelo"} <= labels


async def test_the_page_has_no_client_only(tmp_path: Path) -> None:
    await run_with_proposal(tmp_path)
    page = (tmp_path / "report.html").read_text(encoding="utf-8")

    assert agent_script.SIGNED_VALUE not in page
    assert "client_only" not in page


async def test_data_cannot_close_the_script_block(tmp_path: Path) -> None:
    data = await run_with_proposal(tmp_path, HOSTILE)
    page = ResultsPage.render(data)

    assert "<script>alert" not in page
    assert payload_of(page).executions[0].answer == HOSTILE


async def test_the_page_is_rewritten_with_the_judge_and_links_the_trace(tmp_path: Path) -> None:
    driver = agent_script.ScriptedDriver(
        lambda _: agent_script.answer_events("Não."), trace_id="abc123"
    )
    data = await support.run_items(tmp_path, driver, [(ITEM, 1)])
    files = RunFiles(tmp_path)
    prefixed = data.manifest.model_copy(update={"trace_url_prefix": "https://lf/traces/"})
    files.manifest.write_text(prefixed.model_dump_json(), encoding="utf-8")
    JsonLines.append(files.judge_verdicts, judged_as("TR-01#1", CriterionOutcome.UNKNOWN))
    RunReport.write(files)

    execution = payload_of(files.page.read_text(encoding="utf-8")).executions[0]
    assert execution.trace_url == "https://lf/traces/abc123"
    assert execution.judge_outcome is CriterionOutcome.UNKNOWN
    assert execution.criteria[0].reasoning == "Raciocínio do juiz."
    assert "| Vereditos unknown do juiz | 1 |" in files.report.read_text(encoding="utf-8")


def judged_with(key: str, outcomes: tuple[CriterionOutcome, ...]) -> JudgedVerdict:
    criteria = tuple(
        CriterionVerdict(criterion=number, reasoning="Raciocínio.", verdict=outcome)
        for number, outcome in enumerate(outcomes, start=1)
    )
    return JudgedVerdict(id=key, criteria=criteria, judge_model="claude-sonnet-5-5")


async def test_criteria_approved_count_judged_ones_and_leave_unknown_apart(tmp_path: Path) -> None:
    rubric = ITEM.model_copy(update={"rubric": ("Um", "Dois", "Três")})
    driver = agent_script.ScriptedDriver(lambda _: agent_script.answer_events("Não."))
    await support.run_items(tmp_path, driver, [(rubric, 2)])
    files = RunFiles(tmp_path)
    JsonLines.append(files.judge_verdicts, judged_with("TR-01#1", (PASS, PASS, FAIL)))
    JsonLines.append(files.judge_verdicts, judged_with("TR-01#2", (PASS, UNKNOWN, UNKNOWN)))
    RunReport.write(files)

    assert "| Critérios da rubrica aprovados | 3 de 4 (75.0%) |" in files.report.read_text("utf-8")
    indicators = payload_of(files.page.read_text("utf-8")).indicators
    assert ("Critérios aprovados", "3 de 4 (75.0%)") in [(i.label, i.value) for i in indicators]


async def test_without_a_judged_run_the_criteria_say_so(tmp_path: Path) -> None:
    await run_with_proposal(tmp_path)
    assert "| Critérios da rubrica aprovados | sem julgamento |" in (
        tmp_path / "report.md"
    ).read_text("utf-8")


async def test_without_a_prefix_or_a_trace_the_link_is_absent(tmp_path: Path) -> None:
    await run_with_proposal(tmp_path)
    payload = payload_of((tmp_path / "report.html").read_text(encoding="utf-8"))
    assert payload.executions[0].trace_url is None


def record_verdicts(files: RunFiles) -> None:
    for index, item_id in enumerate(ITEM_IDS):
        outcome = CriterionOutcome.APPROVED if index % 2 else CriterionOutcome.REJECTED
        JsonLines.append(files.judge_verdicts, judged_as(item_id + "#1", outcome))


async def data_with_verdicts(directory: Path) -> RunData:
    driver = agent_script.ScriptedDriver(lambda _: agent_script.answer_events("Resposta"))
    items = [(question(id=item_id, facts=[]), 1) for item_id in ITEM_IDS]
    await support.run_items(directory, driver, items)
    record_verdicts(RunFiles(directory))
    return RunReport.write(RunFiles(directory))


async def test_the_review_sample_is_stable_balanced_and_varied(tmp_path: Path) -> None:
    data = await data_with_verdicts(tmp_path)

    sample = ReviewSample.of(data)

    assert sample == ReviewSample.of(data)
    outcomes = [card.judge_verdict for card in sample]
    assert outcomes.count(CriterionOutcome.APPROVED) == 10
    assert outcomes.count(CriterionOutcome.REJECTED) == 10
    assert {card.area for card in sample} == {"FI", "PR"}


async def test_the_review_leaves_unknown_out(tmp_path: Path) -> None:
    data = await run_with_proposal(tmp_path)
    files = RunFiles(tmp_path)
    JsonLines.append(files.judge_verdicts, judged_as("TR-01#1", CriterionOutcome.UNKNOWN))
    assert ReviewSample.of(RunData.load(files)) == ()
    assert data.records


async def test_a_line_separator_in_an_answer_does_not_break_the_jsonl(tmp_path: Path) -> None:
    data = await run_with_proposal(tmp_path, HOSTILE)
    assert len(data.records) == 2
    assert data.records[0].answer == HOSTILE


async def test_a_review_card_shows_the_earlier_questions_only_when_there_are_any(
    tmp_path: Path,
) -> None:
    driver = agent_script.ScriptedDriver(lambda _: agent_script.answer_events("Resposta"))
    earlier = question(id="TR-13", facts=[], history=["Como fiquei na AV1?"])
    await support.run_items(tmp_path, driver, [(earlier, 1), (question(id="FI-01", facts=[]), 1)])
    for key in ("TR-13#1", "FI-01#1"):
        JsonLines.append(RunFiles(tmp_path).judge_verdicts, judged_as(key, PASS))
    data = RunReport.write(RunFiles(tmp_path))

    histories = {card.execution: card.history for card in ReviewSample.of(data)}
    assert histories == {"TR-13#1": ("Como fiquei na AV1?",), "FI-01#1": ()}
