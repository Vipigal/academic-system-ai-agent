from collections import defaultdict
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime
from operator import attrgetter

from api.domain.lms.material import CourseMaterial
from api.persistence.lms.models import LmsCourseModuleRow, LmsCourseRow, LmsLogRow
from api.persistence.lms.vocabulary import CourseLabel, LmsVocabulary
from api.persistence.sag.catalog_models import SubjectRow


@dataclass(frozen=True, slots=True)
class MaterialSources:
    courses: Sequence[LmsCourseRow]
    modules: Sequence[LmsCourseModuleRow]
    views: Sequence[LmsLogRow]
    subjects: Sequence[SubjectRow]


@dataclass(frozen=True, slots=True)
class MaterialIndex:
    labels: dict[str, CourseLabel]
    names: dict[str, str]
    views: defaultdict[str, list[datetime]]


class MaterialMapper:
    @classmethod
    def to_entities(cls, sources: MaterialSources) -> list[CourseMaterial]:
        index = cls._index(sources)
        materials = [
            cls._material(module, index)
            for module in sources.modules
            if module.course_id in index.labels
        ]
        ordered = sorted(materials, key=cls._order)
        return sorted(ordered, key=attrgetter("term"), reverse=True)

    @staticmethod
    def _order(item: CourseMaterial) -> tuple[str, int, str]:
        return item.subject_code, item.section, item.module_id

    @classmethod
    def _index(cls, sources: MaterialSources) -> MaterialIndex:
        labeled = {row.id: CourseLabel.of(row.shortname) for row in sources.courses}
        return MaterialIndex(
            labels={key: label for key, label in labeled.items() if label is not None},
            names={subject.code: subject.name for subject in sources.subjects},
            views=cls._views_by_module(sources.views),
        )

    @staticmethod
    def _material(module: LmsCourseModuleRow, index: MaterialIndex) -> CourseMaterial:
        label = index.labels[module.course_id]
        return CourseMaterial(
            module_id=module.id,
            subject_code=label.subject_code,
            subject_name=index.names[label.subject_code],
            term=label.term,
            name=module.name,
            kind=LmsVocabulary.material_kind(module.kind),
            section=int(module.section),
            views=tuple(sorted(index.views[module.id])),
        )

    @staticmethod
    def _views_by_module(rows: Sequence[LmsLogRow]) -> defaultdict[str, list[datetime]]:
        grouped: defaultdict[str, list[datetime]] = defaultdict(list)
        for row in rows:
            grouped[row.module_id].append(LmsVocabulary.brasilia(row.time_created))
        return grouped
