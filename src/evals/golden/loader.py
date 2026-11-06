from dataclasses import dataclass
from pathlib import Path

import yaml
from pydantic import TypeAdapter

from evals.golden.items import AttackItem, GoldenItem, ProtocolActionItem, QuestionItem

GOLDEN_DIRECTORY = Path(__file__).parent
QUESTIONS_FILE = GOLDEN_DIRECTORY / "questions.yaml"
RED_TEAM_FILE = GOLDEN_DIRECTORY / "redteam.yaml"
PROTOCOL_ACTIONS_FILE = GOLDEN_DIRECTORY / "protocol_actions.yaml"


@dataclass(frozen=True, slots=True)
class GoldenSet:
    questions: tuple[QuestionItem, ...]
    attacks: tuple[AttackItem, ...]
    actions: tuple[ProtocolActionItem, ...] = ()

    @property
    def catalog_items(self) -> tuple[GoldenItem, ...]:
        return (*self.questions, *self.attacks)

    @property
    def items(self) -> tuple[GoldenItem, ...]:
        return (*self.catalog_items, *self.actions)


class GoldenLoader:
    @classmethod
    def load(
        cls,
        questions_file: Path = QUESTIONS_FILE,
        red_team_file: Path = RED_TEAM_FILE,
        actions_file: Path = PROTOCOL_ACTIONS_FILE,
    ) -> GoldenSet:
        return GoldenSet(
            cls._read(TypeAdapter(tuple[QuestionItem, ...]), questions_file),
            cls._read(TypeAdapter(tuple[AttackItem, ...]), red_team_file),
            cls._read(TypeAdapter(tuple[ProtocolActionItem, ...]), actions_file),
        )

    @staticmethod
    def _read[I](adapter: TypeAdapter[I], path: Path) -> I:
        return adapter.validate_python(yaml.safe_load(path.read_text(encoding="utf-8")))
