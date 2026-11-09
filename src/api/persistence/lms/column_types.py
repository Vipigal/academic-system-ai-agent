from datetime import datetime
from typing import override

from sqlalchemy import Dialect

from api.domain.lms.exam import AttemptState, ExamKind
from api.domain.lms.material import MaterialKind
from api.persistence.core.column_types import BRASILIA, SourceText, TextFlag
from api.persistence.core.source_enum import SourceEnum

NEVER = "0"
EXAM_KIND = SourceEnum(
    {
        "AV1 - Online Exam": ExamKind.AV1,
        "AV2 - Online Exam": ExamKind.AV2,
        "Practice Test": ExamKind.PRACTICE_TEST,
    }
)
ATTEMPT_STATE = SourceEnum.by_value(AttemptState)
MATERIAL_KIND = SourceEnum.by_value(MaterialKind)
SUSPENDED = TextFlag("1", "0")


class EpochMoment(SourceText[datetime]):
    cache_ok = True

    @override
    def to_source(self, value: datetime) -> str:
        return str(int(value.timestamp()))

    @override
    def from_source(self, text: str) -> datetime:
        return datetime.fromtimestamp(int(text), BRASILIA)


class OptionalEpochMoment(EpochMoment):
    cache_ok = True

    @override
    def process_bind_param(self, value: datetime | None, dialect: Dialect) -> str | None:
        return NEVER if value is None else self.to_source(value)

    @override
    def process_result_value(self, value: str | None, dialect: Dialect) -> datetime | None:
        return None if value in {None, NEVER} else super().process_result_value(value, dialect)
