import asyncio
import json
import tempfile
from collections.abc import Awaitable, Callable, Sequence
from dataclasses import dataclass

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from evals.judge.agent_file import JudgeAgent
from evals.judge.port import JudgeAnswer, JudgeBatch, JudgeFailedError
from evals.judge.verdicts import JudgeRequest

CLAUDE_COMMAND = "claude"
PROCESS_TIMEOUT_SECONDS = 600
SHOWN_ERROR_LENGTH = 300
ISOLATION = (
    "--tools",
    "",
    "--strict-mcp-config",
    "--setting-sources",
    "",
    "--settings",
    json.dumps({"autoMemoryEnabled": False}),
    "--disable-slash-commands",
    "--no-session-persistence",
)


@dataclass(frozen=True, slots=True)
class ProcessResult:
    returncode: int
    stdout: str
    stderr: str


type ProcessCall = Callable[[Sequence[str], str], Awaitable[ProcessResult]]


class ClaudeResult(BaseModel):
    model_config = ConfigDict(extra="ignore", frozen=True)

    is_error: bool = False
    result: str | None = None
    model_usage: dict[str, object] = Field(default_factory=dict, alias="modelUsage")


class IsolatedProcess:
    @staticmethod
    async def run(arguments: Sequence[str], text: str) -> ProcessResult:
        with tempfile.TemporaryDirectory() as neutral_directory:
            process = await asyncio.create_subprocess_exec(
                *arguments,
                cwd=neutral_directory,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            try:
                async with asyncio.timeout(PROCESS_TIMEOUT_SECONDS):
                    stdout, stderr = await process.communicate(text.encode())
            except TimeoutError as error:
                process.kill()
                raise JudgeFailedError("O claude -p passou do tempo limite") from error
        return ProcessResult(process.returncode or 0, stdout.decode(), stderr.decode())


class ClaudeCodeArguments:
    @classmethod
    def of(cls, agent: JudgeAgent) -> list[str]:
        return [
            CLAUDE_COMMAND,
            "-p",
            *cls._agent(agent),
            *ISOLATION,
            "--output-format",
            "json",
        ]

    @staticmethod
    def _agent(agent: JudgeAgent) -> list[str]:
        definition = agent.definition()
        return ["--agents", definition, "--agent", agent.name, "--model", agent.model]


class ClaudeCodeJudge:
    def __init__(self, agent: JudgeAgent, process: ProcessCall = IsolatedProcess.run) -> None:
        self._arguments = ClaudeCodeArguments.of(agent)
        self._process = process
        self._model = agent.model

    @property
    def model(self) -> str:
        return self._model

    async def judge(self, batch: Sequence[JudgeRequest]) -> JudgeAnswer:
        prompt = JudgeBatch(items=tuple(batch)).model_dump_json()
        return self._answer_of(await self._process(self._arguments, prompt))

    def _answer_of(self, finished: ProcessResult) -> JudgeAnswer:
        try:
            parsed = ClaudeResult.model_validate_json(finished.stdout)
        except ValidationError as error:
            raise JudgeFailedError(self._failure(finished)) from error
        if parsed.is_error or parsed.result is None:
            raise JudgeFailedError(self._failure(finished, parsed.result))
        if self._model not in parsed.model_usage:
            used = sorted(parsed.model_usage)
            raise JudgeFailedError(f"O juiz rodou em {used}, e não em {self._model}")
        return JudgeAnswer.from_text(parsed.result)

    @staticmethod
    def _failure(finished: ProcessResult, detail: str | None = None) -> str:
        shown = (detail or finished.stderr or finished.stdout)[:SHOWN_ERROR_LENGTH]
        return f"O claude -p falhou ({finished.returncode}): {shown}"
