from collections import defaultdict
from collections.abc import Collection, Iterable, Sequence
from dataclasses import dataclass
from datetime import datetime

from api.domain.protocol import Protocol
from api.domain.protocol_catalog import Service
from api.domain.protocol_document import ProtocolDocument
from api.domain.protocol_message import ProtocolMessage
from api.domain.protocol_status import ProtocolStatusChange
from api.persistence.brasilia import BrasiliaTime
from api.persistence.secretary.models import (
    DemandTypeRow,
    IssuedDocumentRow,
    ProtocolHistoryRow,
    ProtocolInteractionRow,
    ProtocolRow,
)
from api.persistence.secretary.vocabulary import (
    DocumentVocabulary,
    ProtocolVocabulary,
    ServiceVocabulary,
    UnitVocabulary,
)


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
            area=ServiceVocabulary.area(row.area),
            sla_hours=int(row.sla_hours),
            fee=ServiceVocabulary.fee(row.fee),
            active=ServiceVocabulary.is_active(row.active),
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
            type=DocumentVocabulary.document_type(row.document_type),
            issued_at=BrasiliaTime.from_utc(row.issued_at),
            validation_code=row.validation_code,
            delivery=DocumentVocabulary.delivery(row.delivery),
        )

    @staticmethod
    def _change(row: ProtocolHistoryRow) -> ProtocolStatusChange:
        return ProtocolStatusChange(
            status=ProtocolVocabulary.status(row.to_status),
            changed_at=BrasiliaTime.from_utc(row.changed_at),
        )

    @staticmethod
    def _message(row: ProtocolInteractionRow) -> ProtocolMessage:
        return ProtocolMessage(
            id=row.id,
            sender=ProtocolVocabulary.sender(row.author_type),
            text=row.message,
            created_at=BrasiliaTime.from_utc(row.created_at),
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
            status=ProtocolVocabulary.status(row.status),
            resolution=ProtocolVocabulary.resolution(row.resolution),
            requester=ProtocolVocabulary.requester(row.requester_type),
            brand=brand,
            modality=modality,
            enrollment_reference=reference if reference in own else None,
            course_label=row.course_label,
            opened_at=BrasiliaTime.from_utc(row.opened_at),
            first_response_at=ProtocolMapper._optional_moment(row.first_response_at),
            due_at=BrasiliaTime.from_utc(row.due_at),
            closed_at=ProtocolMapper._optional_moment(row.closed_at),
            documents=children.documents,
            history=children.history,
            messages=children.messages,
        )

    @staticmethod
    def _optional_moment(value: str | None) -> datetime | None:
        return None if value is None else BrasiliaTime.from_utc(value)
