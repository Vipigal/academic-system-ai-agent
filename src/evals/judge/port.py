from collections.abc import Sequence
from typing import Protocol, Self

from pydantic import ValidationError

from evals.dataset.parts import FrozenModel
from evals.judge.verdicts import ItemVerdict, JudgeRequest

SHOWN_TEXT_LENGTH = 300
OBJECT_START = "{"
OBJECT_END = "}"


class JudgeFailedError(RuntimeError):
    pass


class JudgeAnswer(FrozenModel):
    verdicts: tuple[ItemVerdict, ...]

    @classmethod
    def from_text(cls, text: str) -> Self:
        start = text.find(OBJECT_START)
        end = text.rfind(OBJECT_END) + 1
        try:
            return cls.model_validate_json(text[start:end])
        except ValidationError as error:
            shown = text[:SHOWN_TEXT_LENGTH]
            raise JudgeFailedError(f"Resposta fora do esquema do juiz: {shown}") from error


class JudgeBatch(FrozenModel):
    items: tuple[JudgeRequest, ...]


class Judge(Protocol):
    @property
    def model(self) -> str: ...

    async def judge(self, batch: Sequence[JudgeRequest]) -> JudgeAnswer: ...
