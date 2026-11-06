import json
from collections.abc import Sequence

import pytest

from api.bootstrap import settings as bootstrap_settings
from evals.judge.agent_file import AGENT_FILE, JudgeAgent
from evals.judge.claude_code import ClaudeCodeJudge, ProcessResult
from evals.judge.port import JudgeAnswer, JudgeFailedError
from evals.judge.reserve import RESERVE_MODEL, ChatModelCompletion, ReserveJudge
from evals.judge.verdicts import CriterionOutcome, CriterionVerdict, ItemVerdict, JudgeRequest
from tests.unit.evals.judge_support import AGENT, JUDGE_MODEL, REQUEST, SECRET_URL, verdict_for


def answer_text(*requests: JudgeRequest) -> str:
    return JudgeAnswer(verdicts=tuple(map(verdict_for, requests))).model_dump_json()


class FakeProcess:
    def __init__(self, result: ProcessResult) -> None:
        self._result = result
        self.arguments: list[str] = []
        self.text = ""

    async def __call__(self, arguments: Sequence[str], text: str) -> ProcessResult:
        self.arguments = list(arguments)
        self.text = text
        return self._result


def finished(
    result: str, *, is_error: bool = False, code: int = 0, model: str = JUDGE_MODEL
) -> ProcessResult:
    usage = {model: {"inputTokens": 1}}
    stdout = json.dumps({"is_error": is_error, "result": result, "modelUsage": usage})
    return ProcessResult(code, stdout, "")


ONE_REQUEST = [REQUEST]


def value_of(arguments: list[str], flag: str) -> str:
    return arguments[arguments.index(flag) + 1]


@pytest.mark.parametrize(
    ("flag", "value"),
    [
        pytest.param("--agent", "eval-judge", id="agent"),
        pytest.param("--model", JUDGE_MODEL, id="pinned-model"),
        pytest.param("--tools", "", id="no-tools"),
        pytest.param("--setting-sources", "", id="no-claude-md"),
        pytest.param("--settings", '{"autoMemoryEnabled": false}', id="no-memory"),
    ],
)
async def test_the_headless_call_isolates_the_judge(flag: str, value: str) -> None:
    process = FakeProcess(finished(answer_text(REQUEST)))
    await ClaudeCodeJudge(AGENT, process).judge(ONE_REQUEST)
    assert process.arguments[:2] == ["claude", "-p"]
    assert value_of(process.arguments, flag) == value


async def test_the_headless_call_has_no_mcp_session_or_slash_commands() -> None:
    process = FakeProcess(finished(answer_text(REQUEST)))
    await ClaudeCodeJudge(AGENT, process).judge(ONE_REQUEST)
    for flag in ("--strict-mcp-config", "--no-session-persistence", "--disable-slash-commands"):
        assert flag in process.arguments


async def test_the_agent_goes_inline_without_tools_and_with_the_schema() -> None:
    process = FakeProcess(finished(answer_text(REQUEST)))
    await ClaudeCodeJudge(AGENT, process).judge(ONE_REQUEST)
    definition = json.loads(value_of(process.arguments, "--agents"))["eval-judge"]
    assert definition["tools"] == []
    assert "verdicts" in definition["prompt"]


async def test_the_request_carries_only_the_fields_of_the_judge() -> None:
    process = FakeProcess(finished(answer_text(REQUEST)))
    await ClaudeCodeJudge(AGENT, process).judge(ONE_REQUEST)

    sent = json.loads(process.text)
    assert sent == {"items": [REQUEST.model_dump(mode="json")]}
    assert set(sent["items"][0]) == {"id", "question", "answer", "reference", "rubric", "history"}


async def test_the_answer_is_validated_against_the_schema() -> None:
    judge = ClaudeCodeJudge(AGENT, FakeProcess(finished('{"verdicts": [{"id": "x"}]}')))
    with pytest.raises(JudgeFailedError, match="fora do esquema"):
        await judge.judge(ONE_REQUEST)


@pytest.mark.parametrize(
    "result",
    [
        pytest.param(finished("Limite de uso atingido", is_error=True, code=1), id="plan-limit"),
        pytest.param(ProcessResult(1, "não é json", "falhou"), id="not-json"),
    ],
)
async def test_a_failed_call_raises_with_the_reason(result: ProcessResult) -> None:
    with pytest.raises(JudgeFailedError, match="claude -p falhou"):
        await ClaudeCodeJudge(AGENT, FakeProcess(result)).judge(ONE_REQUEST)


async def test_a_judge_that_ran_on_another_model_fails() -> None:
    process = FakeProcess(finished(answer_text(REQUEST), model="claude-sonnet-outro"))
    with pytest.raises(JudgeFailedError, match="não em claude-sonnet-5-5"):
        await ClaudeCodeJudge(AGENT, process).judge(ONE_REQUEST)


@pytest.mark.parametrize(
    ("outcomes", "expected"),
    [
        pytest.param(("pass", "pass"), CriterionOutcome.APPROVED, id="all-pass"),
        pytest.param(("pass", "unknown"), CriterionOutcome.UNKNOWN, id="unknown-does-not-pass"),
        pytest.param(("unknown", "fail"), CriterionOutcome.REJECTED, id="fail-wins"),
    ],
)
def test_the_item_outcome_comes_from_the_criteria(
    outcomes: tuple[str, str], expected: CriterionOutcome
) -> None:
    criteria = tuple(
        CriterionVerdict(criterion=number, reasoning="Motivo.", verdict=CriterionOutcome(value))
        for number, value in enumerate(outcomes, start=1)
    )
    verdict = ItemVerdict(id="X#1", criteria=criteria)
    assert verdict.outcome is expected
    assert verdict.passed is (expected is CriterionOutcome.APPROVED)


def test_the_schema_of_the_judge_offers_pass_fail_and_unknown() -> None:
    schema = AGENT.system_prompt()
    assert all(f'"{value}"' in schema for value in ("pass", "fail", "unknown"))


def test_the_agent_prompt_treats_technical_identifiers_as_recognition() -> None:
    prompt = JudgeAgent.load().prompt
    assert "identificador técnico" in prompt
    assert "`unknown`" in prompt


def test_the_agent_file_declares_no_tools_and_loads_the_prompt() -> None:
    frontmatter = AGENT_FILE.read_text(encoding="utf-8").split("---\n")[1]
    assert "tools: []" in frontmatter
    agent = JudgeAgent.load()
    assert agent.name == "eval-judge"
    assert agent.model == JUDGE_MODEL
    assert "reasoning" in agent.prompt


class FakeCompletion:
    def __init__(self, text: str) -> None:
        self._text = text
        self.system = ""

    async def complete(self, system: str, prompt: str) -> str:
        self.system = system
        assert json.loads(prompt)["items"][0]["id"] == REQUEST.id
        return self._text


async def test_the_reserve_sends_the_same_request_and_accepts_fenced_json() -> None:
    completion = FakeCompletion(f"```json\n{answer_text(REQUEST)}\n```")
    answer = await ReserveJudge(AGENT, completion).judge(ONE_REQUEST)
    assert answer.verdicts[0].passed
    assert AGENT.prompt in completion.system


async def test_the_reserve_rejects_an_answer_out_of_the_schema() -> None:
    with pytest.raises(JudgeFailedError):
        await ReserveJudge(AGENT, FakeCompletion("Não sei.")).judge(ONE_REQUEST)


def test_the_reserve_uses_its_own_model_over_the_settings() -> None:
    settings = bootstrap_settings.Settings(database_url=SECRET_URL, agent_model="fake")
    assert ChatModelCompletion.settings_of(settings).agent_model == RESERVE_MODEL


async def test_the_chat_model_completion_goes_through_the_bootstrap_model() -> None:
    settings = bootstrap_settings.Settings(database_url=SECRET_URL, agent_model="fake")
    judge = ReserveJudge(AGENT, ChatModelCompletion(settings))
    with pytest.raises(JudgeFailedError):
        await judge.judge(ONE_REQUEST)


async def test_the_judge_receives_the_earlier_questions_as_context() -> None:
    process = FakeProcess(finished(answer_text(REQUEST)))
    request = REQUEST.model_copy(update={"history": ("Como fiquei na AV1?",)})
    await ClaudeCodeJudge(AGENT, process).judge([request])
    assert json.loads(process.text)["items"][0]["history"] == ["Como fiquei na AV1?"]
