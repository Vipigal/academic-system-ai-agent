from dataclasses import dataclass
from pathlib import Path

import yaml
from pydantic import TypeAdapter

from evals.golden.items import AttackItem, GoldenItem, QuestionItem

GOLDEN_DIRECTORY = Path(__file__).parent
QUESTIONS_FILE = GOLDEN_DIRECTORY / "questions.yaml"
RED_TEAM_FILE = GOLDEN_DIRECTORY / "redteam.yaml"


@dataclass(frozen=True, slots=True)
class GoldenSet:
    questions: tuple[QuestionItem, ...]
    attacks: tuple[AttackItem, ...]

    @property
    def items(self) -> tuple[GoldenItem, ...]:
        return (*self.questions, *self.attacks)


class GoldenLoader:
    @staticmethod
    def load(
        questions_file: Path = QUESTIONS_FILE, red_team_file: Path = RED_TEAM_FILE
    ) -> GoldenSet:
        questions = TypeAdapter(tuple[QuestionItem, ...]).validate_python(
            yaml.safe_load(questions_file.read_text(encoding="utf-8"))
        )
        attacks = TypeAdapter(tuple[AttackItem, ...]).validate_python(
            yaml.safe_load(red_team_file.read_text(encoding="utf-8"))
        )
        return GoldenSet(questions, attacks)
