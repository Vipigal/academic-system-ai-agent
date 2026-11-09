from uuid import uuid4

import pytest
from sqlalchemy import ClauseElement, Executable, event, select, update
from sqlalchemy.orm import ORMExecuteState, Session

from api.domain.identity.session import StudentSession
from api.persistence.agent.models import ConversationRow
from api.persistence.core.database import Database
from api.persistence.core.ownership import OwnershipError
from api.persistence.core.ownership_criteria import STUDENT, OwnershipCriteria
from api.persistence.finance.models import ContractRow, InvoiceRow, PaymentRow, ProductRow

PERSON = "3000178"
STUDENT_SESSION = StudentSession(
    person_ids=frozenset({PERSON}), cpf="01234567890", enrollment_keys=frozenset()
)
CONTRACT_RULE = "(finance.contract.companycode, finance.contract.businessarea"
INVOICE_RULE = "finance.invoice.contractid IN (SELECT finance.contract.contractid"
PAYMENT_RULE = "finance.payment.invoiceid IN (SELECT finance.invoice.invoiceid"


UNUSED_URL = "postgresql+asyncpg://unused@localhost/unused"


class StatementCapturedError(Exception):
    pass


class CapturedSql:
    def __init__(self, info: dict[str, object]) -> None:
        self.session = Session(info=info)
        self.sql = ""
        event.listen(self.session, "do_orm_execute", self._capture)

    def run(self, statement: Executable) -> str:
        with pytest.raises(StatementCapturedError):
            self.session.execute(statement)
        return self.sql

    def _capture(self, state: ORMExecuteState) -> None:
        statement = state.statement
        assert isinstance(statement, ClauseElement)
        compiled = statement.compile()
        self.sql = " ".join(str(compiled).split())
        raise StatementCapturedError


@pytest.fixture
def owned() -> CapturedSql:
    return CapturedSql({STUDENT: STUDENT_SESSION})


def test_the_sessions_of_the_database_carry_the_listener() -> None:
    session_class = Database(UNUSED_URL).db_session_factory.class_.sync_session_class
    assert event.contains(session_class, "do_orm_execute", OwnershipCriteria.apply)


def test_a_child_table_without_join_is_filtered_up_to_the_root(owned: CapturedSql) -> None:
    sql = owned.run(select(PaymentRow))
    assert PAYMENT_RULE in sql
    assert INVOICE_RULE in sql
    assert CONTRACT_RULE in sql


def test_a_join_with_a_wrong_condition_keeps_each_table_filtered(owned: CapturedSql) -> None:
    statement = select(PaymentRow).join(InvoiceRow, PaymentRow.id == PaymentRow.id)
    sql = owned.run(statement)
    assert sql.count(INVOICE_RULE) == 2
    assert PAYMENT_RULE in sql


def test_an_update_carries_the_owner_of_the_session(owned: CapturedSql) -> None:
    statement = (
        update(ConversationRow).where(ConversationRow.id == uuid4()).values(person_id="other")
    )
    sql = owned.run(statement)
    assert sql.startswith("UPDATE agent.conversation")
    assert "agent.conversation.person_id IN (__[POSTCOMPILE_person_id_1])" in sql


def test_a_query_marked_to_skip_ownership_is_left_as_written() -> None:
    sql = CapturedSql({}).run(select(InvoiceRow).execution_options(skip_ownership=True))
    assert "contractid IN" not in sql


def test_a_database_session_without_student_is_refused() -> None:
    with pytest.raises(OwnershipError):
        CapturedSql({}).run(select(InvoiceRow))


def test_a_public_table_is_not_filtered(owned: CapturedSql) -> None:
    sql = owned.run(select(ProductRow))
    assert "WHERE" not in sql


def test_a_core_table_without_model_is_refused(owned: CapturedSql) -> None:
    with pytest.raises(OwnershipError):
        owned.run(select(ContractRow.__table__))
