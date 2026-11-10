import re
from collections.abc import Iterable
from dataclasses import dataclass
from typing import Self

from api.domain.academic.record import Delivery
from api.persistence.core.source_enum import SourceEnum
from api.persistence.lms.column_types import MATERIAL_KIND
from api.persistence.lms.dialect import TENANT_BY_BRAND
from api.persistence.lms.models import LmsCourseRow

COURSE_SHORTNAME = re.compile(
    r"(?P<subject>[A-Z]+\d+)_(?P<year>\d{4})-(?P<semester>\d)_(?P<delivery>[A-Z]+)_"
)
ONLINE_DELIVERY = "EAD"
VIEW_EVENTS = [rf"\mod_{kind}\event\course_module_viewed" for kind in MATERIAL_KIND.sources]
TENANT_BRAND = SourceEnum.inverse_of(TENANT_BY_BRAND)


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

    @classmethod
    def by_course(cls, courses: Iterable[LmsCourseRow]) -> dict[str, Self]:
        labeled = {course.id: cls.of(course.shortname) for course in courses}
        return {key: label for key, label in labeled.items() if label is not None}
