from collections.abc import Iterable, Iterator
from enum import StrEnum
from pathlib import Path
from typing import Self

import yaml
from pydantic import TypeAdapter, model_validator

from evals.dataset.items import DatasetItem
from evals.dataset.loader import DATASET_DIRECTORY
from evals.dataset.parts import FrozenModel
from evals.judge.verdicts import JudgeRequest

CALIBRATION_FILE = DATASET_DIRECTORY / "calibration.yaml"


class CalibrationLabel(StrEnum):
    CORRECT = "correct"
    TAMPERED = "tampered"


class Tampering(StrEnum):
    VALUE = "value"
    DATE = "date"
    OPENED = "opened"
    OBJECT = "object"


class CalibrationCase(FrozenModel):
    id: str
    item: str
    label: CalibrationLabel
    tampering: Tampering | None = None
    answer: str

    @model_validator(mode="after")
    def _tampering_matches_label(self) -> Self:
        if (self.label is CalibrationLabel.TAMPERED) != (self.tampering is not None):
            raise ValueError(f"{self.id}: só a resposta adulterada declara a adulteração")
        return self


class CalibrationCases:
    @staticmethod
    def load(path: Path = CALIBRATION_FILE) -> tuple[CalibrationCase, ...]:
        content = yaml.safe_load(path.read_text(encoding="utf-8"))
        return TypeAdapter(tuple[CalibrationCase, ...]).validate_python(content)

    @staticmethod
    def requests_of(
        cases: Iterable[CalibrationCase], items: Iterable[DatasetItem]
    ) -> Iterator[JudgeRequest]:
        by_id = {item.id: item for item in items}
        for case in cases:
            item = by_id[case.item]
            yield JudgeRequest(
                id=case.id,
                question=item.question,
                answer=case.answer,
                reference=item.reference,
                rubric=item.rubric,
            )
