from datetime import date
from decimal import Decimal

from sqlalchemy.orm import Mapped, mapped_column

from api.domain.academic.enrollment import EnrollmentStatus, Shift, TermStatus
from api.domain.shared.brand import Modality
from api.persistence.core.base import Base
from api.persistence.core.column_types import IsoDate, TextDecimal
from api.persistence.core.source_enum import SourceEnum
from api.persistence.sag.column_types import MODALITY

SAG_SCHEMA = {"schema": "sag"}


class PersonRow(Base):
    __tablename__ = "person"
    __table_args__ = SAG_SCHEMA

    id: Mapped[str] = mapped_column("person_id", primary_key=True)


class EnrollmentRow(Base):
    __tablename__ = "enrollment"
    __table_args__ = SAG_SCHEMA

    brand: Mapped[str] = mapped_column(primary_key=True)
    student_id: Mapped[str] = mapped_column(primary_key=True)
    person_id: Mapped[str]
    course_id: Mapped[str] = mapped_column("course")
    curriculum_id: Mapped[str]
    unit_id: Mapped[str]
    modality: Mapped[Modality] = mapped_column(MODALITY)
    shift: Mapped[Shift] = mapped_column(SourceEnum.by_name(Shift))
    entry_term: Mapped[str]
    semester: Mapped[str]
    completion_pct: Mapped[Decimal] = mapped_column("current_curriculum_completion", TextDecimal())
    gpa: Mapped[Decimal | None] = mapped_column(TextDecimal())
    status: Mapped[EnrollmentStatus] = mapped_column(
        "enrollment_status", SourceEnum.by_name(EnrollmentStatus)
    )
    status_date: Mapped[date] = mapped_column(IsoDate())
    origin_brand: Mapped[str | None]
    origin_student_id: Mapped[str | None]


class EnrollmentHistoryRow(Base):
    __tablename__ = "enrollment_status_history"
    __table_args__ = SAG_SCHEMA

    id: Mapped[str] = mapped_column("history_id", primary_key=True)
    brand: Mapped[str]
    student_id: Mapped[str]
    term: Mapped[str]
    event_date: Mapped[date] = mapped_column(IsoDate())
    old_status: Mapped[EnrollmentStatus | None] = mapped_column(
        SourceEnum.by_name(EnrollmentStatus)
    )
    new_status: Mapped[EnrollmentStatus] = mapped_column(SourceEnum.by_name(EnrollmentStatus))
    reason: Mapped[str]


class TermEnrollmentRow(Base):
    __tablename__ = "term_enrollment"
    __table_args__ = SAG_SCHEMA

    brand: Mapped[str] = mapped_column(primary_key=True)
    student_id: Mapped[str] = mapped_column(primary_key=True)
    term: Mapped[str] = mapped_column(primary_key=True)
    term_status: Mapped[TermStatus] = mapped_column(SourceEnum.by_name(TermStatus))
