from sqlalchemy import and_

from api.persistence.core.base import Base
from api.persistence.core.ownership import OwnershipRule, Public, Via
from api.persistence.secretary.dialect import SecretaryDialect
from api.persistence.secretary.models import (
    DemandTypeRow,
    IssuedDocumentRow,
    ProtocolHistoryRow,
    ProtocolInteractionRow,
    ProtocolRow,
)

PUBLIC_MESSAGE = "False"

SECRETARY_OWNERSHIP: dict[type[Base], OwnershipRule] = {
    ProtocolRow: lambda session: ProtocolRow.id.in_(
        SecretaryDialect.protocols_of(session.cpf, session.enrollment_keys)
    ),
    ProtocolHistoryRow: Via(ProtocolRow, ProtocolHistoryRow.protocol_id == ProtocolRow.id),
    ProtocolInteractionRow: Via(
        ProtocolRow,
        and_(
            ProtocolInteractionRow.protocol_id == ProtocolRow.id,
            ProtocolInteractionRow.is_internal_note == PUBLIC_MESSAGE,
        ),
    ),
    IssuedDocumentRow: Via(ProtocolRow, IssuedDocumentRow.protocol_id == ProtocolRow.id),
    DemandTypeRow: Public(),
}
