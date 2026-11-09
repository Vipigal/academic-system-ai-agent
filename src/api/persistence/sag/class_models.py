from decimal import Decimal

from sqlalchemy.orm import Mapped, mapped_column

from api.domain.academic.enrollment import Shift
from api.domain.academic.record import Delivery, SubjectResult
from api.persistence.core.base import Base
from api.persistence.core.column_types import TextDecimal
from api.persistence.core.source_enum import SourceEnum
from api.persistence.sag.column_types import YES_NO
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
    shift: Mapped[Shift] = mapped_column(SourceEnum.by_name(Shift))
    delivery: Mapped[Delivery] = mapped_column(SourceEnum.by_name(Delivery))
    professor_id: Mapped[str]


class StudentClassRow(Base):
    __tablename__ = "student_class"
    __table_args__ = SAG_SCHEMA

    class_id: Mapped[str] = mapped_column(primary_key=True)
    brand: Mapped[str] = mapped_column(primary_key=True)
    student_id: Mapped[str] = mapped_column(primary_key=True)
    is_retake: Mapped[bool] = mapped_column(YES_NO)
    grade_av1: Mapped[Decimal | None] = mapped_column(TextDecimal())
    grade_av2: Mapped[Decimal | None] = mapped_column(TextDecimal())
    grade_av3: Mapped[Decimal | None] = mapped_column(TextDecimal())
    final_grade: Mapped[Decimal | None] = mapped_column(TextDecimal())
    attendance_pct: Mapped[Decimal | None] = mapped_column(TextDecimal())
    result: Mapped[SubjectResult] = mapped_column(SourceEnum.by_name(SubjectResult))


class ProfessorRow(Base):
    __tablename__ = "professor"
    __table_args__ = SAG_SCHEMA

    id: Mapped[str] = mapped_column("professor_id", primary_key=True)
    full_name: Mapped[str]
    brand: Mapped[str]
    email: Mapped[str]
