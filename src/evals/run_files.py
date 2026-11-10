from dataclasses import dataclass
from pathlib import Path

from pydantic import BaseModel


class LegacyNames:
    @staticmethod
    def renamed(data: object, names: dict[str, str]) -> object:
        if not isinstance(data, dict):
            return data
        return {names.get(key, key): value for key, value in data.items()}


class JsonLines:
    @staticmethod
    def append(path: Path, line: BaseModel) -> None:
        with path.open("a", encoding="utf-8") as output:
            output.write(f"{line.model_dump_json()}\n")

    @staticmethod
    def read[M: BaseModel](path: Path, model: type[M]) -> list[M]:
        if not path.exists():
            return []
        lines = path.read_text(encoding="utf-8").split("\n")
        return [model.model_validate_json(line) for line in lines if line]


@dataclass(frozen=True, slots=True)
class RunFiles:
    directory: Path

    @property
    def manifest(self) -> Path:
        return self.directory / "run.json"

    @property
    def executions(self) -> Path:
        return self.directory / "executions.jsonl"

    @property
    def judge_requests(self) -> Path:
        return self.directory / "judge_requests.jsonl"

    @property
    def judge_verdicts(self) -> Path:
        return self.directory / "judge_verdicts.jsonl"
