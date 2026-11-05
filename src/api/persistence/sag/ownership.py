from api.persistence.base import Base
from api.persistence.ownership import OwnershipRule
from api.persistence.sag.models import EnrollmentRow, PersonRow

SAG_OWNERSHIP: dict[type[Base], OwnershipRule] = {
    PersonRow: lambda session: PersonRow.id.in_(session.person_ids),
    EnrollmentRow: lambda session: EnrollmentRow.person_id.in_(session.person_ids),
}
