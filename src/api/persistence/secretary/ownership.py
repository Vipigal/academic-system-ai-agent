from sqlalchemy import and_, select

from api.persistence.core.ownership import PUBLIC, OwnershipMap
from api.persistence.secretary.dialect import SecretaryDialect
from api.persistence.secretary.models import (
    DemandTypeRow,
    IssuedDocumentRow,
    ProtocolHistoryRow,
    ProtocolInteractionRow,
    ProtocolRow,
)

PUBLIC_MESSAGE = "False"

SECRETARY_OWNERSHIP: OwnershipMap = {
    ProtocolRow: lambda session: ProtocolRow.id.in_(
        SecretaryDialect.protocols_of(session.cpf, session.enrollment_keys)
    ),
    ProtocolHistoryRow: lambda _: ProtocolHistoryRow.protocol_id.in_(select(ProtocolRow.id)),
    ProtocolInteractionRow: lambda _: and_(
        ProtocolInteractionRow.protocol_id.in_(select(ProtocolRow.id)),
        ProtocolInteractionRow.is_internal_note == PUBLIC_MESSAGE,
    ),
    IssuedDocumentRow: lambda _: IssuedDocumentRow.protocol_id.in_(select(ProtocolRow.id)),
    DemandTypeRow: PUBLIC,
}
