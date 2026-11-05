from api.persistence.base import Base
from api.persistence.lms.models import LmsUserRow
from api.persistence.ownership import OwnershipRule

LMS_OWNERSHIP: dict[type[Base], OwnershipRule] = {
    LmsUserRow: lambda session: LmsUserRow.id.in_(session.lms_user_ids),
}
