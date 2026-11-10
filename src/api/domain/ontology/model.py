from dataclasses import dataclass
from enum import Enum


class Area(Enum):
    ACADEMIC_ENROLLMENT = "academic_enrollment"
    ACADEMIC_PERFORMANCE = "academic_performance"
    FINANCE = "finance"
    PROTOCOLS = "protocols"
    LMS = "lms"
    OVERVIEW = "overview"
    LIMITS = "limits"


class RelationKind(Enum):
    COMPOSED_OF = "composed_of"
    LEADS_TO = "leads_to"
    NOT_IMPLIES = "not_implies"
    NOT_SAME_AS = "not_same_as"


@dataclass(frozen=True, slots=True)
class Relation:
    kind: RelationKind
    target: str
    note: str


@dataclass(frozen=True, slots=True, kw_only=True)
class Ontology:
    key: str
    name: str
    area: Area
    synonyms: tuple[str, ...]
    definition: str
    caveat: str | None = None
    never_say: tuple[str, ...]
    relations: tuple[Relation, ...] = ()
