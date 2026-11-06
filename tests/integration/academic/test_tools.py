from datetime import date

from api.application.agent.tools.registry import ToolRegistry
from api.application.shared.page import PageRequest
from api.application.shared.tool_result import DataState, ToolStatus
from api.domain.academic.enrollment import EnrollmentStatus, Shift, TermStatus
from api.domain.academic.record import SubjectResult
from api.domain.shared.brand import Modality
from api.persistence.core.database import Database
from tests.integration.academic import support
from tests.integration.support.sql_oracle import SqlOracle
from tests.integration.support.tools import REFERENCE

ALL_ROWS = PageRequest(limit=100)
ADS_2024_SUBJECTS = (
    "SELECT subject_code FROM sag.curriculum_subject WHERE curriculum_id = 'ADS-2024'"
)


async def test_the_six_tools_are_in_the_registry(database: Database) -> None:
    tools = await support.tools_for(database, support.SAO_PAULO_PERSON)

    registered = {tool.definition.name for tool in ToolRegistry(tools).tools}

    assert registered == {
        "get_academic_calendar",
        "list_course_offers",
        "list_enrollments",
        "get_curriculum",
        "list_subject_records",
        "list_subject_professors",
    }


async def test_du01_calendar_of_the_current_term(database: Database) -> None:
    tools = await support.tools_for(database, support.SAO_PAULO_PERSON)

    result = await tools.get_academic_calendar()

    assert result.data is not None
    term = result.data.term.value
    assert term is not None
    assert (term.term, term.av2_start, term.end_date) == (
        support.CURRENT_TERM,
        date(2026, 12, 5),
        date(2026, 12, 15),
    )
    assert await SqlOracle().values(
        "SELECT av2_start || ' ' || end_date FROM sag.term WHERE is_current = 'Y'"
    ) == {f"{term.av2_start} {term.end_date}"}
    assert (result.data.reference_date, result.caveats) == (REFERENCE, ())


async def test_sr04_term_after_the_last_one_is_not_recorded_with_the_caveat(
    database: Database,
) -> None:
    tools = await support.tools_for(database, support.SAO_PAULO_PERSON)

    result = await tools.get_academic_calendar("2027/1")

    assert result.data is not None
    assert (result.data.term.state, result.data.last_registered_term.end_date) == (
        DataState.NOT_RECORDED,
        date(2026, 12, 15),
    )
    assert support.caveat_keys(result) == {"calendario_2027"}
    assert result.coverage is not None
    assert result.coverage.from_date == date(2021, 2, 1)


async def test_du02_third_semester_comes_from_the_student_curriculum(database: Database) -> None:
    tools = await support.tools_for(database, support.MIGRATED_ADS_PERSON)

    found = support.rows(await tools.get_curriculum(semester=3))

    subjects = {subject.code: subject for subject in found}
    assert set(subjects) == await SqlOracle().values(f"{ADS_2024_SUBJECTS} AND semester = '3'")
    assert set(subjects) == {"ADS0301", "ADS0302", "ADS5303", "ADS0304"}
    assert {subject.curriculum for subject in found} == {"ADS-2024"}
    assert (subjects["ADS0304"].mandatory, subjects["ADS0301"].mandatory) == (False, True)


async def test_du03_curriculum_without_final_paper_lists_its_subjects(database: Database) -> None:
    tools = await support.tools_for(database, support.MIGRATED_ADS_PERSON)

    final_paper = await tools.get_curriculum(subject="FINAL PAPER")
    internship = await tools.get_curriculum(subject="SUPERVISED INTERNSHIP")
    project = await tools.get_curriculum(subject="integrative project")

    assert final_paper.status is ToolStatus.NOT_FOUND
    assert internship.status is ToolStatus.NOT_FOUND
    expected = await SqlOracle().values(ADS_2024_SUBJECTS)
    assert support.candidate_codes(final_paper) == expected
    assert support.only(project).semester == 5


async def test_du04_untranslated_name_offers_the_curriculum_as_candidates(
    database: Database,
) -> None:
    tools = await support.tools_for(database, support.MIGRATED_ADS_PERSON)

    untranslated = await tools.get_curriculum(subject="Programação II")
    by_name = await tools.get_curriculum(subject="algorithms and programming ii")

    assert untranslated.status is ToolStatus.NOT_FOUND
    assert "ADS0404" in support.candidate_codes(untranslated)
    assert support.only(by_name).code == "ADS0404"


async def test_du04_prerequisite_comes_with_the_student_situation(database: Database) -> None:
    tools = await support.tools_for(database, support.MIGRATED_ADS_PERSON)

    subject = support.only(await tools.get_curriculum(subject="ADS0404"))

    assert (subject.semester, subject.mandatory) == (4, False)
    assert subject.situation is SubjectResult.APPROVED
    assert subject.prerequisite is not None
    assert (subject.prerequisite.code, subject.prerequisite.name) == (
        "ADS0102",
        "ALGORITHMS AND PROGRAMMING I",
    )
    assert subject.prerequisite.situation is SubjectResult.APPROVED


async def test_du05_online_offers_of_the_student_brand(database: Database) -> None:
    tools = await support.tools_for(database, support.SAO_PAULO_PERSON)

    online = support.rows(await tools.list_course_offers(modality=Modality.ONLINE, page=ALL_ROWS))
    nursing = await tools.list_course_offers(course="NURSING", modality=Modality.ONLINE)

    assert {offer.course_code for offer in online} == {"ADM", "ADS", "CON", "PED"}
    assert {offer.id for offer in online} == await SqlOracle().values(
        "SELECT o.offer_id FROM sag.course_offer o JOIN sag.unit u USING (unit_id) "
        "WHERE u.brand = 'UniSaoPaulo_EAD'"
    )
    assert nursing.status is ToolStatus.EMPTY


async def test_du05_offers_at_the_student_campus(database: Database) -> None:
    tools = await support.tools_for(database, support.SAO_PAULO_PERSON)

    law = support.rows(await tools.list_course_offers(course="LAW", unit="CAMPUS PAULISTA"))
    nursing = await tools.list_course_offers(course="NURSING", unit="CAMPUS PAULISTA")
    untranslated = await tools.list_course_offers(course="Enfermagem")

    assert {offer.shift for offer in law} == {Shift.MORNING, Shift.EVENING}
    assert support.only(nursing).shift is Shift.MORNING
    assert untranslated.status is ToolStatus.NOT_FOUND
    assert "ENF" in support.candidate_codes(untranslated)


async def test_offers_never_leave_the_student_brand(database: Database) -> None:
    tools = await support.tools_for(database, support.SAO_PAULO_PERSON)

    collected = await tools.list_course_offers(page=ALL_ROWS)

    assert {offer.id for offer in support.rows(collected)} == await SqlOracle().values(
        "SELECT o.offer_id FROM sag.course_offer o JOIN sag.unit u USING (unit_id) "
        "WHERE u.brand IN ('UniSaoPaulo', 'UniSaoPaulo_EAD')"
    )
    assert collected.page is not None
    assert collected.page.next_offset is None


async def test_va01_covers_both_enrollments_of_a_person(database: Database) -> None:
    tools = await support.tools_for(database, support.TRANSFERRED_PERSON)

    found = support.rows(await tools.list_enrollments())

    enrollments = {enrollment.enrollment: enrollment for enrollment in found}
    online = enrollments[support.ONLINE_REFERENCE]
    graduated = enrollments[support.GRADUATED_REFERENCE]
    assert (online.status, online.status_date) == (
        EnrollmentStatus.TRANSFERRED,
        date(2024, 7, 11),
    )
    assert (graduated.status, graduated.status_date, graduated.transferred_from) == (
        EnrollmentStatus.GRADUATED,
        date(2025, 7, 20),
        support.ONLINE_REFERENCE,
    )
    assert {enrollment.current_term_registration.state for enrollment in found} == {
        DataState.NOT_RECORDED
    }
    assert [change.new_status for change in graduated.history] == [
        EnrollmentStatus.ACTIVE,
        EnrollmentStatus.GRADUATED,
    ]


async def test_va01_registration_in_the_current_term(database: Database) -> None:
    tools = await support.tools_for(database, support.SAO_PAULO_PERSON)

    enrollment = support.only(await tools.list_enrollments())

    assert enrollment.status is EnrollmentStatus.ACTIVE
    assert enrollment.current_term == support.CURRENT_TERM
    assert enrollment.current_term_registration.value is TermStatus.REGISTERED
    assert await SqlOracle().values(
        "SELECT term_status FROM sag.term_enrollment "
        "WHERE brand = 'UniSaoPaulo' AND student_id = '181722' AND term = '2026/2'"
    ) == {"REGISTERED"}


async def test_re04_class_without_professor_is_left_out(database: Database) -> None:
    tools = await support.tools_for(database, "3000003")
    sections = await SqlOracle().values(
        "SELECT coalesce(professor.email, 'none') FROM sag.class_section "
        "LEFT JOIN sag.professor ON professor.professor_id = class_section.professor_id "
        "WHERE subject_code = 'ADM0103' AND term = '2026/2' "
        "AND class_section.brand LIKE 'UniSaoPaulo%'"
    )

    result = await tools.list_subject_professors("ADM0103")

    assert "none" in sections
    assert result.status is ToolStatus.OK
    assert {professor.email for professor in support.rows(result)} == sections - {"none"}
