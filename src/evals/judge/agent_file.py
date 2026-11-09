import json
from dataclasses import dataclass
from pathlib import Path
from typing import Self

from evals.judge.port import JudgeAnswer

AGENT_FILE = Path(__file__).parents[3] / ".claude" / "agents" / "eval-judge.md"
FRONTMATTER_FENCE = "---\n"
FRONTMATTER_PARTS = 2


@dataclass(frozen=True, slots=True)
class JudgeAgent:
    name: str
    description: str
    model: str
    prompt: str

    @classmethod
    def load(cls, path: Path = AGENT_FILE) -> Self:
        parts = path.read_text(encoding="utf-8").split(FRONTMATTER_FENCE, FRONTMATTER_PARTS)
        lines = parts[1].splitlines()
        fields = dict(line.split(": ", maxsplit=1) for line in lines)
        prompt = parts[2].strip()
        return cls(fields["name"], fields["description"], fields["model"], prompt)

    def system_prompt(self) -> str:
        schema = json.dumps(JudgeAnswer.model_json_schema(), ensure_ascii=False)
        return f"{self.prompt}\n\nEsquema JSON da resposta:\n{schema}"

    def definition(self) -> str:
        body = {"description": self.description, "prompt": self.system_prompt(), "tools": []}
        return json.dumps({self.name: body}, ensure_ascii=False)
