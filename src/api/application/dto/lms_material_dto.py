from datetime import datetime
from typing import Self

from pydantic import BaseModel, ConfigDict

from api.domain.lms_material import CourseMaterial, MaterialKind


class MaterialViewDto(BaseModel):
    model_config = ConfigDict(frozen=True)

    subject_code: str
    subject_name: str
    term: str
    material: str
    kind: MaterialKind
    section: int
    view_count: int
    last_viewed_at: datetime | None

    @classmethod
    def from_entity(cls, material: CourseMaterial) -> Self:
        return cls(
            subject_code=material.subject_code,
            subject_name=material.subject_name,
            term=material.term,
            material=material.name,
            kind=material.kind,
            section=material.section,
            view_count=material.view_count,
            last_viewed_at=material.last_viewed_at,
        )
