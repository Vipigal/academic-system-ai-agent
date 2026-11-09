from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from typing import Self

from api.application.shared.name_search import NameMatch, NameSearch
from api.application.shared.tool_result import Candidate
from api.domain.academic.enrollment import Enrollment
from api.domain.protocol.action_catalog import ServiceActions
from api.domain.protocol.catalog import Service
from api.domain.protocol.request import Protocol


class ProtocolCandidates:
    @staticmethod
    def of_services(services: Iterable[Service]) -> Iterable[Candidate]:
        return (Candidate(code=item.code, name=item.name) for item in services)

    @staticmethod
    def of_protocol_services(protocols: Iterable[Protocol]) -> Iterable[Candidate]:
        return ProtocolCandidates.of_services(item.service for item in protocols)

    @staticmethod
    def search_protocol_services(query: str | None, protocols: Iterable[Protocol]) -> NameMatch:
        candidates = ProtocolCandidates.of_protocol_services(protocols)
        return NameSearch.search(query, candidates, ServiceActions.titles())

    @staticmethod
    def of_protocols(protocols: Iterable[Protocol]) -> tuple[Candidate, ...]:
        return tuple(map(ProtocolCandidates._of_protocol, protocols))

    @staticmethod
    def _of_protocol(protocol: Protocol) -> Candidate:
        return Candidate(code=protocol.number, name=protocol.service.name)


@dataclass(frozen=True, slots=True)
class EnrollmentChoice:
    selected: Enrollment | None
    candidates: tuple[Candidate, ...]

    @classmethod
    def of(cls, enrollments: Sequence[Enrollment], reference: str) -> Self:
        matching = [item for item in enrollments if item.reference == reference]
        return cls(
            selected=matching[0] if len(matching) == 1 else None,
            candidates=tuple(
                Candidate(code=item.reference, name=item.course_name) for item in enrollments
            ),
        )
