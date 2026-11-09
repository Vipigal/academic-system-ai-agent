import pytest
from sqlalchemy import Column, MetaData, String, Table, select
from sqlalchemy.orm import ColumnProperty

from api.bootstrap.app import ApiFactory
from api.persistence.core.base import Base
from api.persistence.core.ownership import OwnershipError
from api.persistence.core.ownership_criteria import OwnershipRegistry
from api.persistence.finance.models import ContractRow
from api.persistence.identity.tables import IDENTITY_METADATA
from api.persistence.lms.models import LmsUserRow
from api.persistence.sag.models import EnrollmentRow, PersonRow
from api.persistence.secretary.models import ProtocolRow


def test_every_mapped_table_declares_ownership() -> None:
    OwnershipRegistry.assert_complete()


def test_startup_check_fails_for_undeclared_table() -> None:
    metadata = MetaData()
    Table("undeclared", metadata, Column("id", String, primary_key=True))
    with pytest.raises(OwnershipError):
        OwnershipRegistry.assert_complete(metadata)


def test_application_does_not_start_with_undeclared_table() -> None:
    table = Table("undeclared", Base.metadata, Column("id", String, primary_key=True))
    try:
        with pytest.raises(OwnershipError):
            ApiFactory.create()
    finally:
        Base.metadata.remove(table)


@pytest.mark.parametrize("table", IDENTITY_METADATA.tables.values(), ids=str)
def test_private_identity_tables_have_no_ownership_and_stay_out_of_the_models(
    table: Table,
) -> None:
    assert table not in Base.metadata.tables.values()
    with pytest.raises(OwnershipError):
        OwnershipRegistry.rule_of(table)


PRIVATE_COLUMNS = frozenset(
    {"cpf", "taxid", "customerid", "requester_cpf", "requester_name", "email", "phone"}
)
PROFESSOR_CONTACT = ("sag.professor", "email")
REQUESTER_COLUMNS = {
    ("secretary.protocol", "requester_cpf"): ProtocolRow.requester_cpf,
    ("secretary.protocol", "requester_name"): ProtocolRow.requester_name,
}


def test_no_model_declares_a_tax_id_or_contact_except_the_professor_email() -> None:
    declared = {
        (table.fullname, column.name)
        for table in Base.metadata.tables.values()
        for column in table.columns
        if column.name in PRIVATE_COLUMNS
    }
    assert declared == {PROFESSOR_CONTACT, *REQUESTER_COLUMNS}
    for attribute in REQUESTER_COLUMNS.values():
        column = attribute.property
        assert isinstance(column, ColumnProperty)
        assert column.deferred
        assert column.raiseload


def test_selecting_the_protocol_row_never_reads_the_requester() -> None:
    compiled = str(select(ProtocolRow).compile())
    assert "requester_type" in compiled
    assert "requester_cpf" not in compiled
    assert "requester_name" not in compiled


@pytest.mark.parametrize("row", [LmsUserRow, ProtocolRow, PersonRow, EnrollmentRow, ContractRow])
def test_identity_tables_of_the_four_systems_declare_ownership(row: type[Base]) -> None:
    assert OwnershipRegistry.rule_of(row.__table__) is not None


def test_the_payer_table_stays_out_of_the_models() -> None:
    assert "finance.customer" not in {table.fullname for table in Base.metadata.tables.values()}


def test_no_model_declares_relationship() -> None:
    relationships = [
        mapper.class_.__name__ for mapper in Base.registry.mappers if mapper.relationships
    ]
    assert relationships == []
