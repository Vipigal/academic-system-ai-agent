from collections.abc import Mapping
from typing import Self

from pydantic import BaseModel, ConfigDict

from api.application.protocol.dto.catalog import ServiceDto
from api.domain.academic.course import CourseNames
from api.domain.academic.enrollment import Enrollment, EnrollmentStatus
from api.domain.protocol.action import ServiceAction
from api.domain.protocol.catalog import Service
from api.domain.protocol.proposal import RefusalReason

STATUS_SEPARATOR = ", "
SUBJECT_NOT_SUPPORTED = (
    "{title} vale para a matrícula no curso, e não existe pedido deste serviço para uma "
    "disciplina. Diga ao aluno que o serviço para a disciplina não existe e pergunte se ele quer o "
    "pedido para o curso inteiro. Só proponha de novo, sem subject, se ele disser que quer o curso "
    "inteiro."
)
ENROLLMENT_STATUS = (
    "A matrícula {enrollment} está com situação {status}, e {title} aceita só matrícula com "
    "situação {accepted}."
)


class ProtocolProposalDto(BaseModel):
    model_config = ConfigDict(frozen=True)

    service: ServiceDto
    title: str
    effect: str
    limit: str | None
    enrollment: str
    course_name: str
    course_name_pt: str | None
    subject: str | None
    requires_student_message: bool
    request_text: str
    requires_confirmation: bool

    @classmethod
    def of(
        cls, service: Service, action: ServiceAction, enrollment: Enrollment, subject: str | None
    ) -> Self:
        return cls(
            service=ServiceDto.from_entity(service),
            title=action.title,
            effect=action.effect,
            limit=action.not_for,
            enrollment=enrollment.reference,
            course_name=enrollment.course_name,
            course_name_pt=CourseNames.portuguese(enrollment.course_code),
            subject=subject,
            requires_student_message=action.requires_student_message,
            request_text=action.request_text,
            requires_confirmation=True,
        )


class ProposalConfirmation:
    @staticmethod
    def block(action: ServiceAction, enrollment: Enrollment) -> Mapping[str, str | None]:
        course = CourseNames.portuguese(enrollment.course_code) or enrollment.course_name
        return {
            "question": action.question_for(course),
            "effect": action.effect,
            "limit": action.not_for,
            "word": action.confirmation_word,
        }


class RefusalExplanation:
    @staticmethod
    def of_subject(action: ServiceAction) -> str:
        return SUBJECT_NOT_SUPPORTED.format(title=action.title)

    @staticmethod
    def of_status(action: ServiceAction, enrollment: Enrollment) -> str:
        accepted = (item.value for item in EnrollmentStatus if action.accepts(item))
        return ENROLLMENT_STATUS.format(
            enrollment=enrollment.reference,
            status=enrollment.status.value,
            title=action.title,
            accepted=STATUS_SEPARATOR.join(accepted),
        )


class ProtocolRefusalDto(BaseModel):
    model_config = ConfigDict(frozen=True)

    reason: RefusalReason
    service: ServiceDto
    existing_protocol: str | None = None

    @classmethod
    def of(cls, reason: RefusalReason, service: Service, existing: str | None = None) -> Self:
        return cls(
            reason=reason, service=ServiceDto.from_entity(service), existing_protocol=existing
        )


type Proposal = ProtocolProposalDto | ProtocolRefusalDto
