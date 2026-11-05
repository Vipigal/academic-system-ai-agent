import pytest
from sqlalchemy import Column, MetaData, String, Table

from api.main import ApiFactory
from api.persistence.base import Base
from api.persistence.ownership import OwnershipError
from api.persistence.ownership_registry import OwnershipRegistry


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


def test_no_model_declares_relationship() -> None:
    relationships = [
        mapper.class_.__name__ for mapper in Base.registry.mappers if mapper.relationships
    ]
    assert relationships == []
