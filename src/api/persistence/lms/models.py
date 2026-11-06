from sqlalchemy.orm import Mapped, mapped_column

from api.persistence.core.base import Base

LMS_SCHEMA = {"schema": "lms"}


class LmsUserRow(Base):
    __tablename__ = "mdl_user"
    __table_args__ = LMS_SCHEMA

    id: Mapped[str] = mapped_column("student_lms_id", primary_key=True)
    tenant_id: Mapped[str]
    student_id: Mapped[str | None]
    suspended: Mapped[str]
    last_access: Mapped[str] = mapped_column("lastaccess")


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
    name: Mapped[str]
    time_open: Mapped[str] = mapped_column("timeopen")
    time_close: Mapped[str] = mapped_column("timeclose")
    time_limit: Mapped[str] = mapped_column("timelimit")
    max_attempts: Mapped[str] = mapped_column("attempts")


class LmsQuizAttemptRow(Base):
    __tablename__ = "mdl_quiz_attempts"
    __table_args__ = LMS_SCHEMA

    id: Mapped[str] = mapped_column(primary_key=True)
    quiz_id: Mapped[str] = mapped_column("quiz")
    user_id: Mapped[str] = mapped_column("userid")
    number: Mapped[str] = mapped_column("attempt")
    state: Mapped[str]
    time_start: Mapped[str] = mapped_column("timestart")
    time_finish: Mapped[str] = mapped_column("timefinish")
    sum_grades: Mapped[str | None] = mapped_column("sumgrades")


class LmsCourseModuleRow(Base):
    __tablename__ = "mdl_course_modules"
    __table_args__ = LMS_SCHEMA

    id: Mapped[str] = mapped_column(primary_key=True)
    course_id: Mapped[str] = mapped_column("course")
    kind: Mapped[str] = mapped_column("modname")
    name: Mapped[str]
    section: Mapped[str]


class LmsLogRow(Base):
    __tablename__ = "mdl_logstore_standard_log"
    __table_args__ = LMS_SCHEMA

    id: Mapped[str] = mapped_column(primary_key=True)
    event_name: Mapped[str] = mapped_column("eventname")
    module_id: Mapped[str] = mapped_column("contextinstanceid")
    user_id: Mapped[str] = mapped_column("userid")
    time_created: Mapped[str] = mapped_column("timecreated")
