from collections.abc import Sequence
from enum import Enum

from api.domain.academic.enrollment import Enrollment
from api.domain.protocol.action_catalog import ServiceActions
from api.domain.protocol.catalog import Service


class Unavailability(Enum):
    SERVICE_INACTIVE = "service_inactive"
    SERVICE_HAS_FEE = "service_has_fee"
    HANDLED_BY_SECRETARY = "handled_by_secretary"
    ENROLLMENT_STATUS = "enrollment_status"


class ServiceAvailability:
    @staticmethod
    def of(service: Service, enrollments: Sequence[Enrollment]) -> Unavailability | None:
        if not service.active:
            return Unavailability.SERVICE_INACTIVE
        if service.has_fee:
            return Unavailability.SERVICE_HAS_FEE
        entry = ServiceActions.proposable(service.code)
        if entry is None:
            return Unavailability.HANDLED_BY_SECRETARY
        if not any(entry.accepts(item.status) for item in enrollments):
            return Unavailability.ENROLLMENT_STATUS
        return None
