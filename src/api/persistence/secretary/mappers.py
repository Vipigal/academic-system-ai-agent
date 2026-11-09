from collections import defaultdict
from collections.abc import Collection, Iterable, Sequence
from dataclasses import dataclass

from api.domain.protocol.catalog import Service
from api.domain.protocol.document import ProtocolDocument
from api.domain.protocol.message import ProtocolMessage
from api.domain.protocol.request import Protocol
from api.domain.protocol.status import ProtocolStatusChange
from api.persistence.secretary.models import (
    DemandTypeRow,
    IssuedDocumentRow,
    ProtocolHistoryRow,
    ProtocolInteractionRow,
    ProtocolRow,
)
from api.persistence.secretary.vocabulary import UnitVocabulary


@dataclass(frozen=True, slots=True)
class ProtocolSources:
    protocols: Iterable[ProtocolRow]
    services: Iterable[DemandTypeRow]
    documents: Iterable[IssuedDocumentRow]
    history: Iterable[ProtocolHistoryRow]
    messages: Iterable[ProtocolInteractionRow]


@dataclass(frozen=True, slots=True)
class ProtocolChildren:
    documents: tuple[ProtocolDocument, ...]
    history: tuple[ProtocolStatusChange, ...]
    messages: tuple[ProtocolMessage, ...]


class ServiceMapper:
    @classmethod
    def to_entities(cls, rows: Iterable[DemandTypeRow]) -> Sequence[Service]:
        ordered = sorted(rows, key=lambda row: row.code)
        return [cls._service(row) for row in ordered]

    @staticmethod
    def _service(row: DemandTypeRow) -> Service:
        return Service(
            code=row.code,
            name=row.name,
            area=row.area,
            sla_hours=int(row.sla_hours),
            fee=row.fee,
            active=row.active,
        )


class ChildMapper:
    def __init__(self, sources: ProtocolSources) -> None:
        self._documents: defaultdict[str, list[ProtocolDocument]] = defaultdict(list)
        self._history: defaultdict[str, list[ProtocolStatusChange]] = defaultdict(list)
        self._messages: defaultdict[str, list[ProtocolMessage]] = defaultdict(list)
        for document in sorted(sources.documents, key=lambda item: (item.issued_at, item.id)):
            self._documents[document.protocol_id].append(self._document(document))
        for change in sorted(sources.history, key=lambda item: int(item.seq)):
            self._history[change.protocol_id].append(self._change(change))
        for message in sorted(sources.messages, key=lambda item: (item.created_at, item.id)):
            self._messages[message.protocol_id].append(self._message(message))

    def of(self, protocol_id: str) -> ProtocolChildren:
        return ProtocolChildren(
            tuple(self._documents[protocol_id]),
            tuple(self._history[protocol_id]),
            tuple(self._messages[protocol_id]),
        )

    @staticmethod
    def _document(row: IssuedDocumentRow) -> ProtocolDocument:
        return ProtocolDocument(
            id=row.id,
            type=row.document_type,
            issued_at=row.issued_at,
            validation_code=row.validation_code,
            delivery=row.delivery,
        )

    @staticmethod
    def _change(row: ProtocolHistoryRow) -> ProtocolStatusChange:
        return ProtocolStatusChange(status=row.to_status, changed_at=row.changed_at)

    @staticmethod
    def _message(row: ProtocolInteractionRow) -> ProtocolMessage:
        return ProtocolMessage(
            id=row.id,
            sender=row.author_type,
            text=row.message,
            created_at=row.created_at,
        )


class ProtocolMapper:
    @classmethod
    def to_entities(
        cls, sources: ProtocolSources, own_references: Collection[str]
    ) -> Sequence[Protocol]:
        services = {item.code: item for item in ServiceMapper.to_entities(sources.services)}
        children = ChildMapper(sources)
        entities = [
            cls._protocol(row, services[row.demand], children.of(row.id), own_references)
            for row in sources.protocols
        ]
        return sorted(entities, key=lambda item: (item.opened_at, item.number), reverse=True)

    @staticmethod
    def _protocol(
        row: ProtocolRow, service: Service, children: ProtocolChildren, own: Collection[str]
    ) -> Protocol:
        brand, modality = UnitVocabulary.unit(row.unit_code)
        reference = UnitVocabulary.enrollment_reference(row.unit_code, row.student_id)
        return Protocol(
            number=row.id,
            service=service,
            status=row.status,
            resolution=row.resolution,
            requester=row.requester_type,
            brand=brand,
            modality=modality,
            enrollment_reference=reference if reference in own else None,
            course_label=row.course_label,
            opened_at=row.opened_at,
            first_response_at=row.first_response_at,
            due_at=row.due_at,
            closed_at=row.closed_at,
            documents=children.documents,
            history=children.history,
            messages=children.messages,
        )
