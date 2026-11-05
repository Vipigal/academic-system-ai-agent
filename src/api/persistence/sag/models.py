from sqlalchemy.orm import Mapped, mapped_column

from api.persistence.base import Base

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
