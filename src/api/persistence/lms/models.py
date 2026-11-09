from datetime import datetime
from decimal import Decimal

from sqlalchemy.orm import Mapped, mapped_column

from api.domain.lms.exam import AttemptState, ExamKind
from api.domain.lms.material import MaterialKind
from api.persistence.core.base import Base
from api.persistence.core.column_types import TextDecimal
from api.persistence.lms.column_types import (
    ATTEMPT_STATE,
    EXAM_KIND,
    MATERIAL_KIND,
    SUSPENDED,
    EpochMoment,
    OptionalEpochMoment,
)

LMS_SCHEMA = {"schema": "lms"}


class LmsUserRow(Base):
    __tablename__ = "mdl_user"
    __table_args__ = LMS_SCHEMA

    id: Mapped[str] = mapped_column("student_lms_id", primary_key=True)
    tenant_id: Mapped[str]
    student_id: Mapped[str | None]
    suspended: Mapped[bool] = mapped_column(SUSPENDED)
    last_access: Mapped[datetime | None] = mapped_column("lastaccess", OptionalEpochMoment())


class LmsEnrolmentRow(Base):
    __tablename__ = "mdl_user_enrolments"
    __table_args__ = LMS_SCHEMA

    id: Mapped[str] = mapped_column(primary_key=True)
    course_id: Mapped[str] = mapped_column("courseid")
    user_id: Mapped[str] = mapped_column("userid")


class LmsCourseRow(Base):
    __tablename__ = "mdl_course"
    __table_args__ = LMS_SCHEMA

    id: Mapped[str] = mapped_column(primary_key=True)
    tenant_id: Mapped[str]
    shortname: Mapped[str]


class LmsQuizRow(Base):
    __tablename__ = "mdl_quiz"
    __table_args__ = LMS_SCHEMA

    id: Mapped[str] = mapped_column(primary_key=True)
    course_id: Mapped[str] = mapped_column("course")
    kind: Mapped[ExamKind] = mapped_column("name", EXAM_KIND)
    time_open: Mapped[datetime] = mapped_column("timeopen", EpochMoment())
    time_close: Mapped[datetime] = mapped_column("timeclose", EpochMoment())
    time_limit: Mapped[str] = mapped_column("timelimit")
    max_attempts: Mapped[str] = mapped_column("attempts")


class LmsQuizAttemptRow(Base):
    __tablename__ = "mdl_quiz_attempts"
    __table_args__ = LMS_SCHEMA

    id: Mapped[str] = mapped_column(primary_key=True)
    quiz_id: Mapped[str] = mapped_column("quiz")
    user_id: Mapped[str] = mapped_column("userid")
    number: Mapped[str] = mapped_column("attempt")
    state: Mapped[AttemptState] = mapped_column(ATTEMPT_STATE)
    time_start: Mapped[datetime] = mapped_column("timestart", EpochMoment())
    time_finish: Mapped[datetime | None] = mapped_column("timefinish", OptionalEpochMoment())
    sum_grades: Mapped[Decimal | None] = mapped_column("sumgrades", TextDecimal())


class LmsCourseModuleRow(Base):
    __tablename__ = "mdl_course_modules"
    __table_args__ = LMS_SCHEMA

    id: Mapped[str] = mapped_column(primary_key=True)
    course_id: Mapped[str] = mapped_column("course")
    kind: Mapped[MaterialKind] = mapped_column("modname", MATERIAL_KIND)
    name: Mapped[str]
    section: Mapped[str]


class LmsLogRow(Base):
    __tablename__ = "mdl_logstore_standard_log"
    __table_args__ = LMS_SCHEMA

    id: Mapped[str] = mapped_column(primary_key=True)
    event_name: Mapped[str] = mapped_column("eventname")
    module_id: Mapped[str] = mapped_column("contextinstanceid")
    user_id: Mapped[str] = mapped_column("userid")
    time_created: Mapped[datetime] = mapped_column("timecreated", EpochMoment())
