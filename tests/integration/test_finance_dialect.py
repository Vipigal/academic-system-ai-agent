import pytest
from sqlalchemy import select

from api.domain.brand import Brand, EnrollmentRef, Modality
from api.persistence.database import Database
from api.persistence.finance.dialect import FinanceDialect
from api.persistence.finance.models import ContractRow
from api.persistence.sag.dialect import SagDialect
from tests.integration.sql_oracle import SqlOracle


async def contracts_of(database: Database, enrollment: EnrollmentRef) -> set[str]:
    statement = select(ContractRow.id).where(FinanceDialect.contract_of([enrollment]))
    async with database.db_session_factory() as db:
        result = await db.scalars(statement)
        return set(result.all())


async def contracts_written_as(
    database: Database, company_code: str, business_area: str, academic_ref: str
) -> set[str]:
    return await SqlOracle(database).values(
        "SELECT contractid FROM finance.contract "
        "WHERE companycode = :company AND businessarea = :area AND academicref = :reference",
        company=company_code,
        area=business_area,
        reference=academic_ref,
    )


@pytest.mark.parametrize(
    ("company_code", "business_area", "academic_ref", "enrollment"),
    [
        pytest.param(
            "1010",
            "PRESENCIAL",
            "18187-0",
            EnrollmentRef(Brand.SAO_PAULO, Modality.IN_PERSON, "18187"),
            id="with-check-digit",
        ),
        pytest.param(
            "1010",
            "PRESENCIAL",
            "18015",
            EnrollmentRef(Brand.SAO_PAULO, Modality.IN_PERSON, "18015"),
            id="without-check-digit",
        ),
        pytest.param(
            "1010",
            "PRESENCIAL",
            "182583",
            EnrollmentRef(Brand.SAO_PAULO, Modality.IN_PERSON, "18258"),
            id="check-digit-without-hyphen",
        ),
        pytest.param(
            "1040",
            "DIGITAL",
            "1253-0",
            EnrollmentRef(Brand.ATLANTICO, Modality.ONLINE, "01253"),
            id="without-leading-zero",
        ),
        pytest.param(
            "1010",
            "DIGITAL",
            " 01233-5 ",
            EnrollmentRef(Brand.SAO_PAULO, Modality.ONLINE, "01233"),
            id="surrounded-by-spaces",
        ),
    ],
)
async def test_finds_the_contract_however_the_reference_is_written(
    database: Database,
    company_code: str,
    business_area: str,
    academic_ref: str,
    enrollment: EnrollmentRef,
) -> None:
    written = await contracts_written_as(database, company_code, business_area, academic_ref)
    assert written
    assert written <= await contracts_of(database, enrollment)


async def test_finance_and_sag_agree_on_the_same_enrollment(database: Database) -> None:
    written = await contracts_written_as(database, "1010", "DIGITAL", "01295-5")
    enrollment = SagDialect.enrollment_ref("UniSaoPaulo_EAD", "012955")
    assert written
    assert written <= await contracts_of(database, enrollment)


async def test_same_student_number_in_other_brand_is_another_contract(database: Database) -> None:
    other_brand = await contracts_written_as(database, "1050", "DIGITAL", "01244-0")
    found = await contracts_of(database, EnrollmentRef(Brand.ATLANTICO, Modality.ONLINE, "01244"))
    assert other_brand
    assert found
    assert not other_brand & found


async def test_no_enrollment_finds_no_contract(database: Database) -> None:
    statement = select(ContractRow.id).where(FinanceDialect.contract_of([]))
    async with database.db_session_factory() as db:
        result = await db.scalars(statement)
        assert not result.all()
