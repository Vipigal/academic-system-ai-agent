import re
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Self

from api.domain.academic_record import Delivery
from api.domain.lms import AttemptState, ExamKind
from api.domain.lms_material import MaterialKind
from api.persistence.brasilia import BrasiliaTime
from api.persistence.dialect_lookup import DialectLookup

COURSE_SHORTNAME = re.compile(
    r"(?P<subject>[A-Z]+\d+)_(?P<year>\d{4})-(?P<semester>\d)_(?P<delivery>[A-Z]+)_"
)
ONLINE_DELIVERY = "EAD"
EXAM_KIND_BY_SOURCE = {
    "AV1 - Online Exam": ExamKind.AV1,
    "AV2 - Online Exam": ExamKind.AV2,
    "Practice Test": ExamKind.PRACTICE_TEST,
}
ATTEMPT_STATE_BY_SOURCE = {state.value: state for state in AttemptState}
MATERIAL_KIND_BY_SOURCE = {kind.value: kind for kind in MaterialKind}
VIEW_EVENTS = [rf"\mod_{kind}\event\course_module_viewed" for kind in MATERIAL_KIND_BY_SOURCE]
NEVER = "0"
SECONDS_PER_MINUTE = 60


@dataclass(frozen=True, slots=True)
class CourseLabel:
    subject_code: str
    term: str
    delivery: Delivery

    @classmethod
    def of(cls, shortname: str) -> Self | None:
        found = COURSE_SHORTNAME.match(shortname)
        if found is None:
            return None
        delivery = Delivery.ONLINE if found["delivery"] == ONLINE_DELIVERY else Delivery.IN_PERSON
        return cls(found["subject"], f"{found['year']}/{found['semester']}", delivery)


class LmsVocabulary:
    @staticmethod
    def exam_kind(source: str) -> ExamKind:
        return DialectLookup.find(EXAM_KIND_BY_SOURCE, source, "quiz")

    @staticmethod
    def attempt_state(source: str) -> AttemptState:
        return DialectLookup.find(ATTEMPT_STATE_BY_SOURCE, source, "attempt_state")

    @staticmethod
    def material_kind(source: str) -> MaterialKind:
        return DialectLookup.find(MATERIAL_KIND_BY_SOURCE, source, "modname")

    @staticmethod
    def brasilia(epoch: str) -> datetime:
        return BrasiliaTime.from_utc(datetime.fromtimestamp(int(epoch), UTC).isoformat())

    @classmethod
    def brasilia_or_none(cls, epoch: str) -> datetime | None:
        return None if epoch == NEVER else cls.brasilia(epoch)

    @staticmethod
    def minutes(seconds: str) -> int:
        return int(seconds) // SECONDS_PER_MINUTE
