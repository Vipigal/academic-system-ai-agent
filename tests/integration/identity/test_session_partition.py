from collections.abc import Iterable

import pytest

from api.domain.identity.session import StudentSession
from tests.integration.support.owned import Owned
from tests.integration.support.sql_oracle import LMS_OWNERS, PROTOCOL_OWNERS, SqlOracle

pytestmark = [pytest.mark.sweep, pytest.mark.slow]
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
PEOPLE = r"SELECT count(DISTINCT regexp_replace(cpf, '\D', '', 'g')) FROM sag.person"
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


@pytest.fixture
def oracle() -> SqlOracle:
    return SqlOracle()


async def owned_by_oracle(oracle: SqlOracle, owners: str) -> set[str]:
    return {pair.rsplit(":", 1)[0] for pair in await oracle.values(owners)}


def joined(identifiers: Iterable[str]) -> str:
    return ",".join(identifiers)


def identifiers_of(everyone: list[Owned], field: str) -> list[str]:
    return [identifier for session in everyone for identifier in getattr(session, field)]


def owned_pairs(everyone: list[Owned], field: str) -> set[str]:
    return {
        f"{identifier}:{session.cpf}"
        for session in everyone
        for identifier in getattr(session, field)
    }


async def test_every_person_loads_a_session(
    everyone: list[StudentSession], oracle: SqlOracle
) -> None:
    assert len(everyone) == await oracle.count(PEOPLE)
    assert all(session.person_ids and session.enrollment_keys for session in everyone)
    assert all(session.brands for session in everyone)


@pytest.mark.parametrize(
    "field",
    ["person_ids", "enrollment_keys", "contract_ids", "lms_user_ids", "protocol_ids"],
)
def test_no_identifier_belongs_to_two_people(owned_by_everyone: list[Owned], field: str) -> None:
    owned = identifiers_of(owned_by_everyone, field)
    assert len(owned) == len(set(owned))


async def test_protocols_resolve_to_the_expected_owner(
    owned_by_everyone: list[Owned], oracle: SqlOracle
) -> None:
    assert owned_pairs(owned_by_everyone, "protocol_ids") == await oracle.values(PROTOCOL_OWNERS)
    owned = await owned_by_oracle(oracle, PROTOCOL_OWNERS)
    assert len(identifiers_of(owned_by_everyone, "protocol_ids")) == len(owned)


async def test_only_third_parties_and_guardians_without_student_are_invisible(
    owned_by_everyone: list[Owned], oracle: SqlOracle
) -> None:
    invisible = await oracle.values(ALL_PROTOCOLS) - set(
        identifiers_of(owned_by_everyone, "protocol_ids")
    )
    third_party = await oracle.values(THIRD_PARTY_PROTOCOLS)
    guardian = await oracle.values(GUARDIAN_PROTOCOLS)
    unowned = await oracle.values(ALL_PROTOCOLS) - await owned_by_oracle(oracle, PROTOCOL_OWNERS)
    assert len(invisible) == len(unowned)
    assert (len(invisible & third_party), len(invisible & guardian)) == (
        len(third_party),
        len(guardian & unowned),
    )
    assert invisible == third_party | (invisible & guardian)


async def test_guardian_protocols_with_the_student_id_stay_with_the_student(
    owned_by_everyone: list[Owned], oracle: SqlOracle
) -> None:
    guardian = await oracle.values(GUARDIAN_PROTOCOLS)
    owned = await owned_by_oracle(oracle, PROTOCOL_OWNERS)
    visible = set(identifiers_of(owned_by_everyone, "protocol_ids"))
    assert len(guardian & visible) == len(guardian & owned)


async def test_lms_accounts_resolve_to_the_expected_owner(
    owned_by_everyone: list[Owned], oracle: SqlOracle
) -> None:
    assert owned_pairs(owned_by_everyone, "lms_user_ids") == await oracle.values(LMS_OWNERS)
    owned = await owned_by_oracle(oracle, LMS_OWNERS)
    assert len(identifiers_of(owned_by_everyone, "lms_user_ids")) == len(owned)


async def test_lms_accounts_reach_the_attempts_of_a5(
    owned_by_everyone: list[Owned], oracle: SqlOracle
) -> None:
    accounts = joined(identifiers_of(owned_by_everyone, "lms_user_ids"))
    reached = await oracle.count(ATTEMPTS_OF_ACCOUNTS, ids=accounts)
    owned = joined(await owned_by_oracle(oracle, LMS_OWNERS))
    assert reached == await oracle.count(ATTEMPTS_OF_ACCOUNTS, ids=owned)
    assert reached < await oracle.count(ALL_ATTEMPTS)


async def test_enrollment_keys_reach_every_subject_record(
    owned_by_everyone: list[Owned], oracle: SqlOracle
) -> None:
    keys = (":".join(key) for key in identifiers_of(owned_by_everyone, "enrollment_keys"))
    reached = await oracle.count(RECORDS_OF_ENROLLMENTS, ids=joined(keys))
    assert reached == await oracle.count(ALL_RECORDS)


async def test_contracts_reach_every_invoice_and_payment(
    owned_by_everyone: list[Owned], oracle: SqlOracle
) -> None:
    contracts = joined(identifiers_of(owned_by_everyone, "contract_ids"))
    invoices = await oracle.count(INVOICES_OF_CONTRACTS, ids=contracts)
    payments = await oracle.count(PAYMENTS_OF_CONTRACTS, ids=contracts)
    assert (invoices, payments) == (
        await oracle.count(ALL_INVOICES),
        await oracle.count(ALL_PAYMENTS),
    )


async def test_self_paid_contracts_are_the_ones_paid_with_the_own_cpf(
    owned_by_everyone: list[Owned], oracle: SqlOracle
) -> None:
    assert owned_pairs(owned_by_everyone, "self_paid_contract_ids") == await oracle.values(
        SELF_PAID_OWNERS
    )
    assert all(
        session.self_paid_contract_ids <= session.contract_ids for session in owned_by_everyone
    )


def test_some_contracts_are_paid_by_someone_else(owned_by_everyone: list[Owned]) -> None:
    assert any(
        session.contract_ids - session.self_paid_contract_ids for session in owned_by_everyone
    )
