from collections import Counter
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Self

from evals.judge.verdicts import JudgedVerdict, JudgeRequest
from evals.records import ExecutionRecord, RunManifest
from evals.run_files import JsonLines, RunFiles


@dataclass(frozen=True, slots=True)
class RunData:
    manifest: RunManifest
    records: tuple[ExecutionRecord, ...]
    verdicts: Mapping[str, JudgedVerdict]
    requests: Mapping[str, JudgeRequest]
    redone_keys: tuple[str, ...] = ()

    @classmethod
    def load(cls, files: RunFiles) -> Self:
        lines = JsonLines.read(files.executions, ExecutionRecord)
        latest = {line.key: line for line in lines}
        return cls(
            RunManifest.model_validate_json(files.manifest.read_text(encoding="utf-8")),
            tuple(latest[key] for key in sorted(latest)),
            {line.id: line for line in JsonLines.read(files.judge_verdicts, JudgedVerdict)},
            {line.id: line for line in JsonLines.read(files.judge_requests, JudgeRequest)},
            cls._redone(lines),
        )

    @property
    def redone_critical(self) -> tuple[str, ...]:
        critical = set(self.manifest.critical_keys)
        return tuple(key for key in self.redone_keys if key in critical)

    @staticmethod
    def _redone(lines: Sequence[ExecutionRecord]) -> tuple[str, ...]:
        repeated = Counter(line.key for line in lines)
        return tuple(sorted(key for key in repeated if repeated[key] > 1))
