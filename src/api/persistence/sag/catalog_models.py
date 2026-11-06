from sqlalchemy.orm import Mapped, mapped_column

from api.persistence.core.base import Base
from api.persistence.sag.models import SAG_SCHEMA


class TermRow(Base):
    __tablename__ = "term"
    __table_args__ = SAG_SCHEMA

    code: Mapped[str] = mapped_column("term", primary_key=True)
    start_date: Mapped[str]
    end_date: Mapped[str]
    av1_start: Mapped[str]
    av2_start: Mapped[str]
    is_current: Mapped[str]


class CourseRow(Base):
    __tablename__ = "course"
    __table_args__ = SAG_SCHEMA

    id: Mapped[str] = mapped_column("course", primary_key=True)
    acronym: Mapped[str] = mapped_column("course_acronym")
    name: Mapped[str] = mapped_column("course_name")


class UnitRow(Base):
    __tablename__ = "unit"
    __table_args__ = SAG_SCHEMA

    id: Mapped[str] = mapped_column("unit_id", primary_key=True)
    brand: Mapped[str]
    name: Mapped[str] = mapped_column("unit_name")
    city: Mapped[str]
    state: Mapped[str] = mapped_column("uf")


class CourseOfferRow(Base):
    __tablename__ = "course_offer"
    __table_args__ = SAG_SCHEMA

    id: Mapped[str] = mapped_column("offer_id", primary_key=True)
    unit_id: Mapped[str]
    course_id: Mapped[str] = mapped_column("course")
    shift: Mapped[str]


class CurriculumRow(Base):
    __tablename__ = "curriculum"
    __table_args__ = SAG_SCHEMA

    id: Mapped[str] = mapped_column("curriculum_id", primary_key=True)
    total_hours: Mapped[str]


class CurriculumSubjectRow(Base):
    __tablename__ = "curriculum_subject"
    __table_args__ = SAG_SCHEMA

    curriculum_id: Mapped[str] = mapped_column(primary_key=True)
    subject_code: Mapped[str] = mapped_column(primary_key=True)
    semester: Mapped[str]
    mandatory: Mapped[str]
    prerequisite_code: Mapped[str | None]


class SubjectRow(Base):
    __tablename__ = "subject"
    __table_args__ = SAG_SCHEMA

    code: Mapped[str] = mapped_column("subject_code", primary_key=True)
    name: Mapped[str] = mapped_column("subject_name")
    hours: Mapped[str]
