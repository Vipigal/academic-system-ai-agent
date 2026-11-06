from sqlalchemy.orm import Mapped, mapped_column

from api.persistence.core.base import Base

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
    modality: Mapped[str]
    shift: Mapped[str]
    entry_term: Mapped[str]
    semester: Mapped[str]
    completion_pct: Mapped[str] = mapped_column("current_curriculum_completion")
    gpa: Mapped[str | None]
    status: Mapped[str] = mapped_column("enrollment_status")
    status_date: Mapped[str]
    origin_brand: Mapped[str | None]
    origin_student_id: Mapped[str | None]


class EnrollmentHistoryRow(Base):
    __tablename__ = "enrollment_status_history"
    __table_args__ = SAG_SCHEMA

    id: Mapped[str] = mapped_column("history_id", primary_key=True)
    brand: Mapped[str]
    student_id: Mapped[str]
    term: Mapped[str]
    event_date: Mapped[str]
    old_status: Mapped[str | None]
    new_status: Mapped[str]
    reason: Mapped[str]


class TermEnrollmentRow(Base):
    __tablename__ = "term_enrollment"
    __table_args__ = SAG_SCHEMA

    brand: Mapped[str] = mapped_column(primary_key=True)
    student_id: Mapped[str] = mapped_column(primary_key=True)
    term: Mapped[str] = mapped_column(primary_key=True)
    term_status: Mapped[str]
