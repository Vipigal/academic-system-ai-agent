from collections.abc import Sequence
from dataclasses import dataclass, field, replace
from datetime import date
from decimal import Decimal

from api.domain.academic.curriculum import EnrollmentProgress
from api.domain.academic.enrollment import Enrollment, EnrollmentStatus, Shift
from api.domain.identity.session import StudentSession
from api.domain.protocol.catalog import Service, ServiceArea
from api.domain.protocol.proposal import SignedProposal
from api.domain.protocol.request import Protocol
from api.domain.shared.brand import Brand, Modality
from api.domain.shared.money import Money

PERSON = "3000003"
SIGNED = "assinatura"
LOCK = Service(
    code="ACA-010",
    name="Enrollment Lock",
    area=ServiceArea.ACADEMIC,
    sla_hours=72,
    fee=Money(0),
    active=True,
)
GRADE_REVIEW = replace(LOCK, code="ACA-020", name="Grade Review", sla_hours=168)
INFORMATION = replace(LOCK, code="GEN-090", name="General Information", area=ServiceArea.GENERAL)
ACTIVE = Enrollment(
    reference="UniSaoPaulo:181722",
    brand=Brand.SAO_PAULO,
    course_code="CON",
    course_name="Accounting",
    curriculum_id="1",
    curriculum_hours=3000,
    unit_name="CAMPUS PAULISTA",
    modality=Modality.IN_PERSON,
    shift=Shift.MORNING,
    status=EnrollmentStatus.ACTIVE,
    status_date=date(2026, 2, 1),
    entry_term="2026-1",
    semester=3,
    completion_pct=Decimal(40),
    gpa=None,
    origin_reference=None,
    registrations={},
    history=(),
)
LOCKED = replace(ACTIVE, reference="UniSaoPaulo:181723", status=EnrollmentStatus.LOCKED)
SESSION = StudentSession(
    person_ids=frozenset({PERSON}), cpf="00000000000", enrollment_keys=frozenset()
)


@dataclass
class FakeProtocols:
    services: Sequence[Service] = (LOCK, GRADE_REVIEW, INFORMATION)
    protocols: Sequence[Protocol] = ()

    async def list_services(self) -> Sequence[Service]:
        return self.services

    async def list_protocols(self) -> Sequence[Protocol]:
        return self.protocols


class FakeAcademic:
    async def list_enrollments(self) -> Sequence[Enrollment]:
        return (ACTIVE, LOCKED)

    async def list_progress(self) -> Sequence[EnrollmentProgress]:
        return ()


@dataclass
class RecordingSigner:
    signed: list[SignedProposal] = field(default_factory=list)

    def sign(self, proposal: SignedProposal) -> str:
        self.signed.append(proposal)
        return SIGNED

    def verify(self, token: str) -> SignedProposal | None:
        return self.signed[-1] if token == SIGNED and self.signed else None
