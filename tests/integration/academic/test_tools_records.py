import asyncio
from decimal import Decimal

from api.application.academic.dto.curriculum import CurriculumFilter
from api.application.academic.dto.record import SubjectRecordDto
from api.application.agent.tool_arguments import BoundedPage
from api.application.shared.tool_result import DataState, ToolResult, ToolStatus
from api.domain.academic.enrollment import Shift
from api.domain.academic.record import SubjectResult
from api.persistence.core.database import Database
from tests.integration.academic import support
from tests.integration.support.sql_oracle import SqlOracle

ATLANTICO_PERSON = "3007823"
CRIMINAL_LAW_PERSON = "3001652"
RETAKE_PERSON = "3000889"
ONLINE_FAILED_PERSON = "3002501"
PERSON_WITHOUT_GPA = "3000414"
UNKNOWN_PERSON = "does-not-exist"
ALL_ROWS = BoundedPage(limit=100)
RECORDS_OF_ENROLLMENT = (
    "SELECT sc.class_id FROM sag.student_class sc "
    "JOIN sag.class_section cs USING (class_id) "
    "WHERE sc.brand = :brand AND sc.student_id = :student"
)


def by_subject(result: ToolResult[list[SubjectRecordDto]]) -> dict[str, SubjectRecordDto]:
    return {record.subject_code: record for record in support.rows(result)}


async def test_va02_subjects_of_the_current_term(database: Database) -> None:
    tools = await support.tools_for(database, support.SAO_PAULO_PERSON)

    result = await tools.list_subject_records(term=support.CURRENT_TERM)

    subjects = by_subject(result)
    assert set(subjects) == await SqlOracle().values(
        "SELECT cs.subject_code FROM sag.student_class sc "
        "JOIN sag.class_section cs USING (class_id) "
        "WHERE sc.brand = 'UniSaoPaulo' AND sc.student_id = '181722' AND cs.term = '2026/2'"
    )
    assert {record.section for record in subjects.values()} == {"T01"}
    assert {record.shift for record in subjects.values()} == {Shift.EVENING}
    assert result.totals == {"in_progress": 4}


async def test_va03_several_matches_and_av2_not_yet(database: Database) -> None:
    tools = await support.tools_for(database, ATLANTICO_PERSON)

    result = await tools.list_subject_records(
        term=support.CURRENT_TERM, subject="software engineering"
    )

    subjects = by_subject(result)
    assert subjects["ADS0203"].av1.value == Decimal("3.3")
    assert subjects["ADS0503"].av1.value == Decimal("5.0")
    assert subjects["ADS0203"].av2.state is DataState.NOT_YET
    assert subjects["ADS0503"].final_grade.state is DataState.NOT_YET
    assert "av" in support.caveat_keys(result)


async def test_va04_required_av2_is_an_estimate_with_its_caveats(database: Database) -> None:
    tools = await support.tools_for(database, CRIMINAL_LAW_PERSON)

    result = await tools.list_subject_records(term=support.CURRENT_TERM, subject="CRIMINAL LAW I")

    record = support.only(result)
    assert record.av1.value == Decimal("4.3")
    assert record.required_av2.value == Decimal("7.1")
    assert {"media", "criterio_de_aprovacao"} <= support.caveat_keys(result)


async def test_va05_failure_by_attendance_and_later_approval(database: Database) -> None:
    tools = await support.tools_for(database, RETAKE_PERSON)

    found = support.rows(await tools.list_subject_records(subject="ADS0204"))

    records = {record.class_id: record for record in found}
    failed = records["223955"]
    approved = records["237516"]
    assert (failed.term, failed.final_grade.value, failed.attendance_pct.value, failed.result) == (
        "2024/2",
        Decimal("6.9"),
        Decimal("75.0"),
        SubjectResult.FAILED_ATTENDANCE,
    )
    assert (approved.final_grade.value, approved.attendance_pct.value, approved.result) == (
        Decimal("7.0"),
        Decimal("83.6"),
        SubjectResult.APPROVED,
    )
    assert approved.required_av2.state is DataState.NOT_RECORDED
    assert found[0].term == "2025/2"


async def test_va06_attendance_below_the_limit_has_the_caveat(database: Database) -> None:
    tools = await support.tools_for(database, support.SAO_PAULO_PERSON)

    result = await tools.list_subject_records(term=support.CURRENT_TERM, subject="BUSINESS LAW")

    assert support.only(result).attendance_pct.value == Decimal("71.2")
    assert "frequencia" in support.caveat_keys(result)


async def test_va07_cr_is_per_enrollment(database: Database) -> None:
    tools = await support.tools_for(database, support.SAO_PAULO_PERSON)

    enrollment = support.only(await tools.list_enrollments())

    assert enrollment.enrollment == support.SAO_PAULO_ENROLLMENT
    assert enrollment.cr.value == Decimal("7.87")


async def test_va07_missing_gpa_is_not_recorded(database: Database) -> None:
    tools = await support.tools_for(database, PERSON_WITHOUT_GPA)

    enrollments = support.rows(await tools.list_enrollments())

    assert DataState.NOT_RECORDED in {enrollment.cr.state for enrollment in enrollments}


async def test_va08_pending_subjects_and_hours_summary(database: Database) -> None:
    tools = await support.tools_for(database, support.MIGRATED_ADS_PERSON)
    key = support.MIGRATED_ADS

    result = await tools.get_curriculum(enrollment=key, filters=CurriculumFilter(pending_only=True))

    found = support.rows(result)
    assert {subject.code: subject.hours for subject in found} == {"ADS5303": 80, "ADS0502": 60}
    assert {subject.situation for subject in found} == {SubjectResult.IN_PROGRESS}
    assert (
        result.totals[f"{key}.total_hours"],
        result.totals[f"{key}.completed_hours"],
        result.totals[f"{key}.completion_pct"],
        result.totals[f"{key}.pending_subjects"],
    ) == (1360, 1220, Decimal("89.71"), 2)
    assert await SqlOracle().values(
        "SELECT current_curriculum_completion FROM sag.enrollment "
        "WHERE brand = 'UniMontanhas' AND student_id = '070017'"
    ) == {"89.71"}


async def test_hours_summary_does_not_change_with_filters_or_page(database: Database) -> None:
    tools = await support.tools_for(database, support.MIGRATED_ADS_PERSON)

    filtered = await tools.get_curriculum(
        filters=CurriculumFilter(semester=1), page=BoundedPage(limit=1)
    )
    complete = await tools.get_curriculum()

    assert filtered.totals == complete.totals


async def test_va09_failures_recorded_before_the_term_ends(database: Database) -> None:
    tools = await support.tools_for(database, ONLINE_FAILED_PERSON)

    result = await tools.list_subject_records(term=support.CURRENT_TERM)

    subjects = by_subject(result)
    failed = [record for record in subjects.values() if record.result is SubjectResult.FAILED]
    assert {record.subject_code for record in failed} == {
        "ADM0402",
        "ADM0403",
        "ADM5401",
        "ADM5404",
    }
    assert {
        (record.final_grade.value, record.av1.state, record.av2.state) for record in failed
    } == {(Decimal("0.0"), DataState.NOT_RECORDED, DataState.NOT_YET)}
    assert result.totals == {"failed": 4}


async def test_online_attendance_is_not_recorded(database: Database) -> None:
    tools = await support.tools_for(database, ONLINE_FAILED_PERSON)

    result = await tools.list_subject_records(term=support.CURRENT_TERM)

    assert {record.attendance_pct.state for record in support.rows(result)} == {
        DataState.NOT_RECORDED
    }
    assert "frequencia" in support.caveat_keys(result)


async def test_re04_professors_show_only_name_and_email(database: Database) -> None:
    tools = await support.tools_for(database, CRIMINAL_LAW_PERSON)

    own, other = support.rows(await tools.list_subject_professors("CRIMINAL LAW I"))

    assert (own.name, own.email, own.teaches_student) == (
        "OTAVIO BORGES",
        "otavio.borges@prof.unimontanhas.example",
        True,
    )
    assert (other.name, other.email, other.unit_name, other.teaches_student) == (
        "GABRIELA ISABEL ABREU DA PAZ",
        "gabriela.dapaz@prof.unimontanhas.example",
        "CAMPUS UBERLANDIA",
        False,
    )
    assert set(own.model_dump()) == {
        "name",
        "email",
        "subject_code",
        "subject_name",
        "term",
        "unit_name",
        "teaches_student",
    }
    cpfs = await SqlOracle().values("SELECT cpf FROM sag.professor")
    assert not cpfs & set(own.model_dump().values())


async def test_re04_ambiguous_name_asks_for_one_subject(database: Database) -> None:
    tools = await support.tools_for(database, CRIMINAL_LAW_PERSON)

    ambiguous = await tools.list_subject_professors("CRIMINAL LAW")
    unknown = await tools.list_subject_professors("Direito Penal")

    assert ambiguous.status is ToolStatus.AMBIGUOUS
    assert {candidate.name for candidate in ambiguous.candidates} >= {
        "CRIMINAL LAW I",
        "CRIMINAL LAW II",
    }
    assert unknown.status is ToolStatus.NOT_FOUND
    assert "CRIMINAL LAW I" in {candidate.name for candidate in unknown.candidates}


async def test_enrollment_of_another_student_answers_like_a_nonexistent_one(
    database: Database,
) -> None:
    tools = await support.tools_for(database, support.MIGRATED_ADS_PERSON)

    foreign = await tools.get_curriculum(enrollment=support.SAO_PAULO_ENROLLMENT)
    nonexistent = await tools.get_curriculum(enrollment="UniSaoPaulo:000000")
    foreign_records = await tools.list_subject_records(enrollment=support.SAO_PAULO_ENROLLMENT)

    assert foreign.status is ToolStatus.NOT_FOUND
    assert foreign == nonexistent
    assert foreign_records.candidates == foreign.candidates
    assert support.candidate_codes(foreign) == {support.MIGRATED_ADS}


async def test_without_enrollment_every_result_says_where_it_belongs(database: Database) -> None:
    tools = await support.tools_for(database, support.TRANSFERRED_PERSON)
    both = {support.ONLINE_REFERENCE, support.GRADUATED_REFERENCE}

    records = support.rows(await tools.list_subject_records(page=ALL_ROWS))
    curriculum = support.rows(await tools.get_curriculum(page=ALL_ROWS))
    filtered = support.rows(
        await tools.list_subject_records(enrollment=support.GRADUATED_REFERENCE, page=ALL_ROWS)
    )

    assert {record.enrollment for record in records} == both
    assert {subject.enrollment for subject in curriculum} == both
    assert {record.class_id for record in filtered} == await SqlOracle().values(
        RECORDS_OF_ENROLLMENT, brand="UniAraucaria", student="090697"
    )


async def test_paginating_records_returns_the_oracle_set_once(database: Database) -> None:
    tools = await support.tools_for(database, support.MIGRATED_ADS_PERSON)
    collected: list[str] = []
    offset: int | None = 0

    while offset is not None:
        result = await tools.list_subject_records(page=BoundedPage(offset=offset, limit=7))
        collected.extend(record.class_id for record in support.rows(result))
        assert result.page is not None
        offset = result.page.next_offset

    assert len(collected) == len(set(collected))
    assert set(collected) == await SqlOracle().values(
        RECORDS_OF_ENROLLMENT, brand="UniMontanhas", student="070017"
    )


async def test_a_person_without_enrollments_gets_empty_results(database: Database) -> None:
    tools = await support.tools_for(database, UNKNOWN_PERSON)

    results = await asyncio.gather(
        tools.list_enrollments(),
        tools.list_subject_records(),
        tools.get_curriculum(),
        tools.list_course_offers(),
        tools.list_subject_professors("LAW"),
    )

    assert [result.status for result in results] == [ToolStatus.EMPTY] * 4 + [ToolStatus.NOT_FOUND]
