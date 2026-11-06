from sqlalchemy.orm import Mapped, mapped_column

from api.persistence.core.base import Base
from api.persistence.sag.models import SAG_SCHEMA


class ClassSectionRow(Base):
    __tablename__ = "class_section"
    __table_args__ = SAG_SCHEMA

    id: Mapped[str] = mapped_column("class_id", primary_key=True)
    term: Mapped[str]
    subject_code: Mapped[str]
    brand: Mapped[str]
    unit_id: Mapped[str | None]
    section: Mapped[str]
    shift: Mapped[str]
    delivery: Mapped[str]
    professor_id: Mapped[str]


class StudentClassRow(Base):
    __tablename__ = "student_class"
    __table_args__ = SAG_SCHEMA

    class_id: Mapped[str] = mapped_column(primary_key=True)
    brand: Mapped[str] = mapped_column(primary_key=True)
    student_id: Mapped[str] = mapped_column(primary_key=True)
    is_retake: Mapped[str]
    grade_av1: Mapped[str | None]
    grade_av2: Mapped[str | None]
    grade_av3: Mapped[str | None]
    final_grade: Mapped[str | None]
    attendance_pct: Mapped[str | None]
    result: Mapped[str]


class ProfessorRow(Base):
    __tablename__ = "professor"
    __table_args__ = SAG_SCHEMA

    id: Mapped[str] = mapped_column("professor_id", primary_key=True)
    full_name: Mapped[str]
    brand: Mapped[str]
    email: Mapped[str]
