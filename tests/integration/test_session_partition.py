from collections.abc import AsyncIterator, Iterable

import pytest
import pytest_asyncio

from api.domain.session import StudentSession
from api.persistence.database import Database
from api.persistence.student_session_repository import StudentSessionRepository
from api.settings import Settings
from tests.integration.sql_oracle import SqlOracle

ONE_ID_PER_PERSON = (
    r"SELECT min(person_id) FROM sag.person GROUP BY regexp_replace(cpf, '\D', '', 'g')"
)
PROTOCOL_OWNERS = r"""
    SELECT protocol.protocol || ':' || regexp_replace(person.cpf, '\D', '', 'g')
    FROM secretary.protocol
    JOIN secretary.unit ON unit.unit_code = protocol.unit_code
    JOIN sag.enrollment
      ON enrollment.brand = replace(translate(unit.brand_name, 'ãáâ', 'aaa'), ' ', '')
         || CASE unit.unit_type WHEN 'Polo EAD' THEN '_EAD' ELSE '' END
    JOIN sag.person ON person.person_id = enrollment.person_id
    WHERE (enrollment.student_id = lpad(protocol.stu_id, 6, '0')
           AND (protocol.requester_type = 'Guardian'
                OR (protocol.requester_type IN ('Student', 'Alumni')
                    AND regexp_replace(person.cpf, '\D', '', 'g')
                        = lpad(protocol.requester_cpf, 11, '0'))))
       OR (protocol.requester_type IN ('Student', 'Alumni')
           AND regexp_replace(person.cpf, '\D', '', 'g') = lpad(protocol.requester_cpf, 11, '0')
           AND NOT EXISTS (SELECT 1 FROM sag.enrollment other
                           WHERE other.student_id = lpad(protocol.stu_id, 6, '0')))
"""
LMS_OWNERS = r"""
    SELECT account.student_lms_id || ':' || regexp_replace(person.cpf, '\D', '', 'g')
    FROM lms.mdl_user account
    JOIN lms.mdl_tenant tenant ON tenant.id = account.tenant_id
    JOIN sag.enrollment
      ON lower(split_part(enrollment.brand, '_', 1)) = tenant.slug
     AND (enrollment.brand LIKE '%\_EAD') = (upper(trim(account.student_id)) LIKE 'EAD\_%')
     AND left(enrollment.student_id, 5) = split_part(trim(account.student_id), '_', 2)
    JOIN sag.person ON person.person_id = enrollment.person_id
"""
SELF_PAID_OWNERS = r"""
    SELECT contract.contractid || ':' || regexp_replace(person.cpf, '\D', '', 'g')
    FROM finance.contract
    JOIN finance.customer ON customer.customerid = contract.customerid
    JOIN sag.enrollment
      ON split_part(enrollment.brand, '_', 1) = CASE contract.companycode
             WHEN '1010' THEN 'UniSaoPaulo'
             WHEN '1020' THEN 'UniMontanhas'
             WHEN '1030' THEN 'UniLitoral'
             WHEN '1040' THEN 'UniAtlantico'
             WHEN '1050' THEN 'UniAraucaria' END
     AND (enrollment.brand LIKE '%\_EAD') = (contract.businessarea = 'DIGITAL')
     AND left(enrollment.student_id, 5)
         = lpad(split_part(trim(contract.academicref), '-', 1), 5, '0')
    JOIN sag.person ON person.person_id = enrollment.person_id
    WHERE customer.taxid = regexp_replace(person.cpf, '\D', '', 'g')
"""
ALL_PROTOCOLS = "SELECT protocol FROM secretary.protocol"
THIRD_PARTY_PROTOCOLS = (
    "SELECT protocol FROM secretary.protocol WHERE requester_type = 'Third Party'"
)
GUARDIAN_PROTOCOLS = "SELECT protocol FROM secretary.protocol WHERE requester_type = 'Guardian'"
ATTEMPTS_OF_ACCOUNTS = (
    "SELECT count(*) FROM lms.mdl_quiz_attempts WHERE userid = ANY(string_to_array(:ids, ','))"
)
ALL_ATTEMPTS = "SELECT count(*) FROM lms.mdl_quiz_attempts"
RECORDS_OF_ENROLLMENTS = (
    "SELECT count(*) FROM sag.student_class "
    "WHERE brand || ':' || student_id = ANY(string_to_array(:ids, ','))"
)
ALL_RECORDS = "SELECT count(*) FROM sag.student_class"
INVOICES_OF_CONTRACTS = (
    "SELECT count(*) FROM finance.invoice WHERE contractid = ANY(string_to_array(:ids, ','))"
)
ALL_INVOICES = "SELECT count(*) FROM finance.invoice"
PAYMENTS_OF_CONTRACTS = (
    "SELECT count(*) FROM finance.payment JOIN finance.invoice USING (invoiceid) "
    "WHERE contractid = ANY(string_to_array(:ids, ','))"
)
ALL_PAYMENTS = "SELECT count(*) FROM finance.payment"


@pytest_asyncio.fixture(scope="module", loop_scope="module")
async def everyone() -> AsyncIterator[list[StudentSession]]:
    database = Database(Settings.from_environment().database_url.get_secret_value())
    people = await SqlOracle(database).values(ONE_ID_PER_PERSON)
    repository = StudentSessionRepository(database.db_session_factory)
    yield [await repository.load(person_id) for person_id in sorted(people)]
    await database.dispose()


@pytest.fixture
def oracle(database: Database) -> SqlOracle:
    return SqlOracle(database)


def joined(identifiers: Iterable[str]) -> str:
    return ",".join(identifiers)


def identifiers_of(everyone: list[StudentSession], field: str) -> list[str]:
    return [identifier for session in everyone for identifier in getattr(session, field)]


def owned_pairs(everyone: list[StudentSession], field: str) -> set[str]:
    return {
        f"{identifier}:{session.cpf}"
        for session in everyone
        for identifier in getattr(session, field)
    }


def test_every_person_loads_a_session(everyone: list[StudentSession]) -> None:
    assert len(everyone) == 1000
    assert all(session.person_ids and session.enrollment_keys for session in everyone)
    assert all(session.brands for session in everyone)


@pytest.mark.parametrize(
    "field",
    ["person_ids", "enrollment_keys", "contract_ids", "lms_user_ids", "protocol_ids"],
)
def test_no_identifier_belongs_to_two_people(everyone: list[StudentSession], field: str) -> None:
    owned = identifiers_of(everyone, field)
    assert len(owned) == len(set(owned))


async def test_protocols_resolve_to_the_expected_owner(
    everyone: list[StudentSession], oracle: SqlOracle
) -> None:
    assert owned_pairs(everyone, "protocol_ids") == await oracle.values(PROTOCOL_OWNERS)
    assert len(identifiers_of(everyone, "protocol_ids")) == 3882


async def test_only_third_parties_and_guardians_without_student_are_invisible(
    everyone: list[StudentSession], oracle: SqlOracle
) -> None:
    invisible = await oracle.values(ALL_PROTOCOLS) - set(identifiers_of(everyone, "protocol_ids"))
    third_party = await oracle.values(THIRD_PARTY_PROTOCOLS)
    guardian = await oracle.values(GUARDIAN_PROTOCOLS)
    assert len(invisible) == 51
    assert (len(third_party), len(invisible & guardian)) == (11, 40)
    assert invisible == third_party | (invisible & guardian)


async def test_guardian_protocols_with_the_student_id_stay_with_the_student(
    everyone: list[StudentSession], oracle: SqlOracle
) -> None:
    guardian = await oracle.values(GUARDIAN_PROTOCOLS)
    assert len(guardian & set(identifiers_of(everyone, "protocol_ids"))) == 73


async def test_lms_accounts_resolve_to_the_expected_owner(
    everyone: list[StudentSession], oracle: SqlOracle
) -> None:
    assert owned_pairs(everyone, "lms_user_ids") == await oracle.values(LMS_OWNERS)
    assert len(identifiers_of(everyone, "lms_user_ids")) == 983


async def test_lms_accounts_reach_the_attempts_of_a5(
    everyone: list[StudentSession], oracle: SqlOracle
) -> None:
    accounts = joined(identifiers_of(everyone, "lms_user_ids"))
    reached = await oracle.count(ATTEMPTS_OF_ACCOUNTS, ids=accounts)
    assert (reached, await oracle.count(ALL_ATTEMPTS)) == (18566, 18857)


async def test_enrollment_keys_reach_every_subject_record(
    everyone: list[StudentSession], oracle: SqlOracle
) -> None:
    keys = (":".join(key) for key in identifiers_of(everyone, "enrollment_keys"))
    reached = await oracle.count(RECORDS_OF_ENROLLMENTS, ids=joined(keys))
    assert (reached, await oracle.count(ALL_RECORDS)) == (20277, 20277)


async def test_contracts_reach_every_invoice_and_payment(
    everyone: list[StudentSession], oracle: SqlOracle
) -> None:
    contracts = joined(identifiers_of(everyone, "contract_ids"))
    invoices = await oracle.count(INVOICES_OF_CONTRACTS, ids=contracts)
    payments = await oracle.count(PAYMENTS_OF_CONTRACTS, ids=contracts)
    assert (invoices, await oracle.count(ALL_INVOICES)) == (25931, 25931)
    assert (payments, await oracle.count(ALL_PAYMENTS)) == (24380, 24380)


async def test_self_paid_contracts_are_the_ones_paid_with_the_own_cpf(
    everyone: list[StudentSession], oracle: SqlOracle
) -> None:
    assert owned_pairs(everyone, "self_paid_contract_ids") == await oracle.values(SELF_PAID_OWNERS)
    assert all(session.self_paid_contract_ids <= session.contract_ids for session in everyone)


def test_some_contracts_are_paid_by_someone_else(everyone: list[StudentSession]) -> None:
    assert any(session.contract_ids - session.self_paid_contract_ids for session in everyone)
