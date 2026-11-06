import hashlib
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Self

from api.domain.ontology.model import Area
from api.domain.ontology.renderer import OntologyRenderer

SKILLS_ROOT = Path(__file__).parent / "skills"
SKILL_FILE = "SKILL.md"
FRONTMATTER_FENCE = "---"
BLOCK_SEPARATOR = "\n\n"


@dataclass(frozen=True, slots=True)
class Skill:
    area: Area
    description: str
    body: str

    @classmethod
    def parse(cls, area: Area, text: str) -> Self:
        _, frontmatter, body = text.split(f"{FRONTMATTER_FENCE}\n", maxsplit=2)
        lines = frontmatter.splitlines()
        fields = dict(line.split(": ", maxsplit=1) for line in lines)
        if fields.get("name") != area.value or not fields.get("description"):
            raise ValueError(f"A skill {area.value} precisa de name e description no frontmatter")
        return cls(area=area, description=fields["description"], body=body.strip())


class SkillLibrary:
    def __init__(self, skills: Mapping[Area, Skill]) -> None:
        self._skills = skills
        self._instructions = {
            area: BLOCK_SEPARATOR.join((skill.body, OntologyRenderer.for_skill(area)))
            for area, skill in skills.items()
        }

    @classmethod
    def load(cls, root: Path = SKILLS_ROOT) -> Self:
        return cls(
            {
                area: Skill.parse(
                    area, (root / area.value / SKILL_FILE).read_text(encoding="utf-8")
                )
                for area in Area
            }
        )

    def instructions(self, area: Area) -> str:
        return self._instructions[area]

    def listing(self) -> str:
        return "\n".join(
            f"- `{area.value}`: {skill.description}" for area, skill in self._skills.items()
        )

    def fingerprint(self) -> str:
        joined = BLOCK_SEPARATOR.join(self._instructions[area] for area in Area)
        return hashlib.sha256(joined.encode()).hexdigest()
