from collections.abc import Mapping, Sequence
from dataclasses import replace
from datetime import datetime, timedelta

from api.domain.finance.invoice import Invoice
from api.domain.protocol.catalog import Service, ServiceArea
from api.domain.protocol.request import Protocol, Requester
from api.domain.protocol.status import ProtocolStatus, Resolution
from api.domain.shared.brand import Brand, Modality
from api.domain.shared.money import Money
from api.persistence.core.brasilia import BRASILIA

GRADE_REVIEW = Service(
    code="ACA-020",
    name="Grade Review",
    area=ServiceArea.ACADEMIC,
    sla_hours=168,
    fee=Money(0),
    active=True,
)
CERTIFICATE = replace(
    GRADE_REVIEW, code="DOC-001", name="Enrollment Certificate", area=ServiceArea.DOCUMENTS
)
UNKNOWN = replace(GRADE_REVIEW, code="XYZ-999", name="Unknown Service")
OPENED = datetime(2026, 7, 10, 9, tzinfo=BRASILIA)
REVIEW = Protocol(
    number="20260013930",
    service=GRADE_REVIEW,
    status=ProtocolStatus.RESOLVED,
    resolution=Resolution.DENIED,
    requester=Requester.SELF,
    brand=Brand.SAO_PAULO,
    modality=Modality.IN_PERSON,
    enrollment_reference="UniSaoPaulo:181722",
    course_label="Accounting",
    opened_at=OPENED,
    first_response_at=None,
    due_at=OPENED + timedelta(hours=168),
    closed_at=OPENED + timedelta(days=7),
    documents=(),
    history=(),
    messages=(),
)
DECLARATION = replace(REVIEW, number="20260000001", service=CERTIFICATE)


class InMemoryProtocols:
    async def list_services(self) -> Sequence[Service]:
        return (GRADE_REVIEW, CERTIFICATE, UNKNOWN)

    async def list_protocols(self) -> Sequence[Protocol]:
        return (REVIEW, DECLARATION)


class NoFees:
    async def list_service_fees(self) -> Mapping[str, Invoice]:
        return {}
