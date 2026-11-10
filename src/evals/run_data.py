from collections.abc import Mapping
from dataclasses import dataclass
from typing import Self

from evals.gate import GateRule, RoundResult
from evals.judge.verdicts import JudgedVerdict, JudgeRequest
from evals.records import ExecutionRecord, RunManifest
from evals.run_files import JsonLines, RunFiles


@dataclass(frozen=True, slots=True)
class RunData:
    manifest: RunManifest
    records: tuple[ExecutionRecord, ...]
    verdicts: Mapping[str, JudgedVerdict]
    requests: Mapping[str, JudgeRequest]

    @classmethod
    def load(cls, files: RunFiles) -> Self:
        lines = JsonLines.read(files.executions, ExecutionRecord)
        latest = {line.key: line for line in lines}
        return cls(
            RunManifest.model_validate_json(files.manifest.read_text(encoding="utf-8")),
            tuple(latest[key] for key in sorted(latest)),
            {line.id: line for line in JsonLines.read(files.judge_verdicts, JudgedVerdict)},
            {line.id: line for line in JsonLines.read(files.judge_requests, JudgeRequest)},
        )

    @property
    def result(self) -> RoundResult:
        return GateRule.result(self.manifest, self.records)
