from api.application.shared.page import PageRequest
from api.application.shared.tool_result import ToolStatus
from api.domain.lms.material import MaterialKind
from api.persistence.core.database import Database
from tests.integration.lms import support
from tests.integration.support.sql_oracle import SqlOracle
from tests.integration.support.tools import all_pages

LAST_ACCESS = (
    "SELECT to_char(to_timestamp(lastaccess::bigint) AT TIME ZONE 'America/Sao_Paulo', "
    "'YYYY-MM-DD HH24:MI') FROM lms.mdl_user WHERE student_lms_id = :user"
)
SAO_PAULO_USER = "100006"
ARAUCARIA_ACTIVE_USER = "100121"
MONTANHAS_USER = "102024"
MODULE_VIEWS = (
    "SELECT count(*) FROM lms.mdl_logstore_standard_log l "
    "JOIN lms.mdl_course_modules m ON m.id = l.contextinstanceid "
    "JOIN lms.mdl_course c ON c.id = m.course "
    "WHERE l.userid = :user AND m.name = 'Week 2 - Class Notes' "
    "AND c.shortname LIKE 'ADM0104_2026-2%' AND l.eventname LIKE '%mod_page%course_module_viewed'"
)


async def test_lm04_last_access_is_converted_to_brasilia(database: Database) -> None:
    tools = await support.tools_for(database, support.SAO_PAULO_PERSON)

    result = await tools.get_lms_account()

    account = support.only(result)
    assert (account.enrollment, account.exists, account.suspended, account.never_accessed) == (
        "UniSaoPaulo_EAD:012157",
        True,
        False,
        False,
    )
    assert str(account.last_access)[:16] == "2026-10-31 23:57"
    assert str(account.last_access)[:16] == await support.single_value(
        LAST_ACCESS, user=SAO_PAULO_USER
    )
    assert support.caveat_keys(result) == set()


async def test_zero_last_access_means_never_accessed_with_the_caveat(database: Database) -> None:
    tools = await support.tools_for(database, support.NEVER_ACCESSED_PERSON)

    result = await tools.get_lms_account()

    account = support.only(result)
    assert (account.exists, account.never_accessed, account.last_access) == (True, True, None)
    assert "ultimo_acesso" in support.caveat_keys(result)


async def test_cr02_active_enrollment_with_debt_is_not_suspended(database: Database) -> None:
    tools = await support.tools_for(database, support.ARAUCARIA_ACTIVE_PERSON)

    result = await tools.get_lms_account()

    account = support.only(result)
    assert (account.suspended, str(account.last_access)[:16]) == (
        False,
        await support.single_value(LAST_ACCESS, user=ARAUCARIA_ACTIVE_USER),
    )
    assert support.caveat_keys(result) == set()


async def test_cr02_enrollment_without_account_is_reported_as_missing(database: Database) -> None:
    tools = await support.tools_for(database, support.ARAUCARIA_NO_ACCOUNT_PERSON)

    account = support.only(await tools.get_lms_account())

    assert account.exists is False
    assert (account.suspended, account.never_accessed, account.last_access) == (None, None, None)


async def test_suspended_account_of_a_closed_enrollment_carries_the_caveat(
    database: Database,
) -> None:
    tools = await support.tools_for(database, support.SUSPENDED_PERSON)

    result = await tools.get_lms_account()

    assert support.only(result).suspended is True
    assert support.caveat_keys(result) == {"suspensao_do_ava"}


async def test_unknown_person_has_no_accounts(database: Database) -> None:
    tools = await support.tools_for(database, support.UNKNOWN_PERSON)

    assert (await tools.get_lms_account()).status is ToolStatus.EMPTY


async def test_lm05_views_of_a_week_page_without_the_content(database: Database) -> None:
    tools = await support.tools_for(database, support.MONTANHAS_PERSON)

    result = await tools.list_material_views(subject="Microeconomics", query="week 2")

    material = support.only(result)
    assert (material.material, material.kind, material.section, material.term) == (
        "Week 2 - Class Notes",
        MaterialKind.PAGE,
        2,
        "2026/2",
    )
    assert material.view_count == 2 == await SqlOracle().count(MODULE_VIEWS, user=MONTANHAS_USER)
    assert str(material.last_viewed_at)[:16] == "2026-10-09 09:19"


async def test_material_without_views_is_listed_with_zero_and_no_date(database: Database) -> None:
    tools = await support.tools_for(database, support.MONTANHAS_PERSON)

    materials = support.rows(await tools.list_material_views(subject="ADM0104"))

    assert {item.kind for item in materials} <= set(MaterialKind)
    unseen = [item for item in materials if item.view_count == 0]
    assert unseen
    assert all(item.last_viewed_at is None for item in unseen)


async def test_unknown_material_query_is_not_found_with_the_subject_materials(
    database: Database,
) -> None:
    tools = await support.tools_for(database, support.MONTANHAS_PERSON)

    result = await tools.list_material_views(subject="Microeconomics", query="semana 2")

    assert result.status is ToolStatus.NOT_FOUND
    assert "Week 2 - Class Notes" in support.candidate_codes(result)


async def test_material_views_paginate_to_the_end(database: Database) -> None:
    tools = await support.tools_for(database, support.MONTANHAS_PERSON)
    whole = await tools.list_material_views(subject="ADM0104", page=PageRequest(limit=100))

    paged = await all_pages(lambda page: tools.list_material_views(subject="ADM0104", page=page), 2)

    assert paged == support.rows(whole)
