from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Self

PROMPTS_ROOT = Path(__file__).parent / "prompts"
CURRENT_VERSION = "student_agent_v2"


@dataclass(frozen=True, slots=True)
class SystemPrompt:
    version: str
    template: str

    @classmethod
    def load(cls, version: str = CURRENT_VERSION, root: Path = PROMPTS_ROOT) -> Self:
        return cls(version=version, template=(root / f"{version}.md").read_text(encoding="utf-8"))

    def render(self, reference_date: date, skills: str) -> str:
        return self.template.format(
            reference_date=reference_date.strftime("%d/%m/%Y"), skills=skills
        )
