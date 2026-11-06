from dataclasses import dataclass
from datetime import datetime
from enum import Enum


class MaterialKind(Enum):
    PAGE = "page"
    RESOURCE = "resource"
    URL = "url"


@dataclass(frozen=True, slots=True)
class CourseMaterial:
    module_id: str
    subject_code: str
    subject_name: str
    term: str
    name: str
    kind: MaterialKind
    section: int
    views: tuple[datetime, ...]

    @property
    def view_count(self) -> int:
        return len(self.views)

    @property
    def last_viewed_at(self) -> datetime | None:
        return max(self.views, default=None)
