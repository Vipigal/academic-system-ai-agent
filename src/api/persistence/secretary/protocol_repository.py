import asyncio
from collections.abc import Sequence

from sqlalchemy import select

from api.domain.protocol import Protocol
from api.domain.protocol_catalog import Service
from api.persistence.repository_adapter import RepositoryAdapter
from api.persistence.sag.dialect import SagDialect
from api.persistence.secretary.mappers import ProtocolMapper, ProtocolSources, ServiceMapper
from api.persistence.secretary.models import (
    DemandTypeRow,
    IssuedDocumentRow,
    ProtocolHistoryRow,
    ProtocolInteractionRow,
    ProtocolRow,
)


class SqlProtocolRepository:
    def __init__(self, adapter: RepositoryAdapter) -> None:
        self._adapter = adapter

    async def list_services(self) -> Sequence[Service]:
        return ServiceMapper.to_entities(await self._adapter.fetch(select(DemandTypeRow)))

    async def list_protocols(self) -> Sequence[Protocol]:
        sources = await asyncio.gather(
            self._adapter.fetch(select(ProtocolRow)),
            self._adapter.fetch(select(DemandTypeRow)),
            self._adapter.fetch(
                select(IssuedDocumentRow).join(
                    ProtocolRow, IssuedDocumentRow.protocol_id == ProtocolRow.id
                )
            ),
            self._adapter.fetch(
                select(ProtocolHistoryRow).join(
                    ProtocolRow, ProtocolHistoryRow.protocol_id == ProtocolRow.id
                )
            ),
            self._adapter.fetch(
                select(ProtocolInteractionRow).join(
                    ProtocolRow, ProtocolInteractionRow.protocol_id == ProtocolRow.id
                )
            ),
        )
        return ProtocolMapper.to_entities(ProtocolSources(*sources), self._own_references())

    def _own_references(self) -> frozenset[str]:
        keys = self._adapter.student_session.enrollment_keys
        return frozenset(SagDialect.reference(brand, student_id) for brand, student_id in keys)
