from sqlalchemy.orm import Mapped, mapped_column

from api.persistence.base import Base

LMS_SCHEMA = {"schema": "lms"}


class LmsUserRow(Base):
    __tablename__ = "mdl_user"
    __table_args__ = LMS_SCHEMA

    id: Mapped[str] = mapped_column("student_lms_id", primary_key=True)
    tenant_id: Mapped[str]
    student_id: Mapped[str | None]
