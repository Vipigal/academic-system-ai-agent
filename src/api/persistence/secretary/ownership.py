from api.persistence.base import Base
from api.persistence.ownership import OwnershipRule
from api.persistence.secretary.models import ProtocolRow

SECRETARY_OWNERSHIP: dict[type[Base], OwnershipRule] = {
    ProtocolRow: lambda session: ProtocolRow.id.in_(session.protocol_ids),
}
