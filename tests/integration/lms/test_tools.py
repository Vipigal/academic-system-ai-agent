from datetime import date
from decimal import Decimal

from api.application.agent.tool_arguments import BoundedPage
from api.application.shared.tool_result import StatedValue, ToolStatus
from api.domain.academic.record import Delivery
from api.domain.lms.exam import AttemptState, ExamKind, ExamWindow
from api.persistence.core.database import Database
from tests.integration.lms import support
from tests.integration.support.sql_oracle import SqlOracle
from tests.integration.support.tools import all_pages

WINDOW_EDGE = (
    "SELECT to_char(to_timestamp(q.{column}::bigint) AT TIME ZONE 'America/Sao_Paulo', "
    "'YYYY-MM-DD HH24:MI') FROM lms.mdl_quiz q JOIN lms.mdl_course c ON c.id = q.course "
    "JOIN lms.mdl_user_enrolments e ON e.courseid = c.id "
    "WHERE e.userid = :user AND c.shortname = :course AND q.name LIKE :name"
)


def minute(value: object) -> str:
    return str(value).replace("T", " ")[:16]


async def test_lm01_window_is_in_brasilia_and_online_av2_has_one_attempt(
    database: Database,
) -> None:
    tools = await support.tools_for(database, support.LITORAL_EAD_PERSON)
    filters = {"user": support.LITORAL_EAD_USER, "course": "ADM0104_2026-2_EAD_T01", "name": "AV2%"}

    result = await tools.list_online_exams(subject="microeconomics", term=support.CURRENT_TERM)

    av2 = next(exam for exam in support.rows(result) if exam.kind is ExamKind.AV2)
    assert (minute(av2.opens_at), minute(av2.closes_at)) == (
        await support.single_value(WINDOW_EDGE.format(column="timeopen"), **filters),
        await support.single_value(WINDOW_EDGE.format(column="timeclose"), **filters),
    )
    assert (minute(av2.closes_at), av2.time_limit_minutes, av2.max_attempts) == (
        "2026-12-12 23:59",
        90,
        1,
    )
    assert (av2.window, av2.delivery, av2.attempts_remaining) == (
        ExamWindow.NOT_OPEN,
        Delivery.ONLINE,
        1,
    )
    assert av2.official_grade == StatedValue[Decimal].not_yet()


async def test_lm01_in_person_class_has_only_practice_tests(database: Database) -> None:
    tools = await support.tools_for(database, support.ARAUCARIA_PERSON)

    exams = support.rows(await tools.list_online_exams(term=support.CURRENT_TERM))

    assert {(exam.kind, exam.delivery, exam.max_attempts) for exam in exams} == {
        (ExamKind.PRACTICE_TEST, Delivery.IN_PERSON, 3)
    }


async def test_lm02_abandoned_attempt_counts_toward_the_limit_with_the_caveat(
    database: Database,
) -> None:
    tools = await support.tools_for(database, support.ARAUCARIA_PERSON)

    result = await tools.list_online_exams(subject="ethics and citizenship")

    exam = support.only(result)
    first, second = exam.attempts
    assert [(a.number, a.state, a.grade, minute(a.started_at)[:10]) for a in (first, second)] == [
        (1, AttemptState.ABANDONED, None, "2026-09-10"),
        (2, AttemptState.FINISHED, Decimal("8.9"), "2026-10-05"),
    ]
    assert (exam.max_attempts, exam.attempts_used, exam.attempts_remaining) == (3, 2, 1)
    assert (minute(exam.closes_at), exam.window, exam.official_grade) == (
        "2026-11-21 23:59",
        ExamWindow.OPEN,
        None,
    )
    assert support.caveat_keys(result) == {"tentativa"}


async def test_lm03_delivered_av1_shows_the_ava_grade_beside_the_official_one(
    database: Database,
) -> None:
    tools = await support.tools_for(database, support.ATLANTICO_PERSON)

    result = await tools.list_online_exams(subject="information security", term="2026/2")

    av1 = next(exam for exam in support.rows(result) if exam.kind is ExamKind.AV1)
    assert (minute(av1.attempts[0].finished_at), av1.ava_grade) == (
        "2026-10-07 23:56",
        Decimal("8.3"),
    )
    assert av1.official_grade == StatedValue[Decimal].recorded(Decimal("8.3"))
    assert support.caveat_keys(result) == set()


async def test_cr04_diverging_grades_are_both_shown(database: Database) -> None:
    tools = await support.tools_for(database, support.MONTANHAS_EAD_PERSON)

    result = await tools.list_online_exams(subject="ADM5504", term="2026/2")

    av1 = next(exam for exam in support.rows(result) if exam.kind is ExamKind.AV1)
    assert (av1.subject_name, av1.ava_grade) == ("DATA-DRIVEN DECISION MAKING", Decimal("7.7"))
    assert av1.official_grade == StatedValue[Decimal].recorded(Decimal("10.0"))
    assert await SqlOracle().values(
        "SELECT grade_av1 FROM sag.student_class WHERE class_id = '252797' "
        "AND brand = 'UniMontanhas_EAD' AND student_id LIKE '01306%'"
    ) == {"10.0"}


async def test_sr05_term_before_the_records_returns_coverage_not_a_denial(
    database: Database,
) -> None:
    tools = await support.tools_for(database, support.LITORAL_EAD_PERSON)

    result = await tools.list_online_exams(term="2022/1")

    assert result.status is ToolStatus.EMPTY
    assert result.coverage is not None
    assert result.coverage.from_date == date(2023, 2, 1)
    assert (
        await SqlOracle().count(
            "SELECT count(*) FROM lms.mdl_quiz_attempts WHERE to_timestamp(timestart::bigint) "
            "< timestamp '2023-02-01'"
        )
        == 0
    )


async def test_term_inside_the_records_has_no_coverage(database: Database) -> None:
    tools = await support.tools_for(database, support.LITORAL_EAD_PERSON)

    result = await tools.list_online_exams(term=support.CURRENT_TERM)

    assert result.coverage is None


async def test_unknown_subject_is_not_found_with_the_students_own_subjects(
    database: Database,
) -> None:
    tools = await support.tools_for(database, support.LITORAL_EAD_PERSON)
    other = await support.tools_for(database, support.UNKNOWN_PERSON)

    result = await tools.list_online_exams(subject="Programação II")
    same_for_nobody = await other.list_online_exams(subject="Programação II")

    assert (result.status, same_for_nobody.status) == (ToolStatus.NOT_FOUND, ToolStatus.NOT_FOUND)
    assert "ADM0104" in support.candidate_codes(result)
    assert support.candidate_codes(same_for_nobody) == set()


async def test_pagination_walks_every_exam_of_the_student(database: Database) -> None:
    tools = await support.tools_for(database, support.LITORAL_EAD_PERSON)
    expected = await SqlOracle().count(
        "SELECT count(*) FROM lms.mdl_quiz q "
        "JOIN lms.mdl_user_enrolments e ON e.courseid = q.course WHERE e.userid = :user",
        user=support.LITORAL_EAD_USER,
    )

    exams = await all_pages(lambda page: tools.list_online_exams(page=page), limit=7)
    one_page = await tools.list_online_exams(page=BoundedPage(limit=100))

    assert len(exams) == expected
    assert exams == support.rows(one_page)
