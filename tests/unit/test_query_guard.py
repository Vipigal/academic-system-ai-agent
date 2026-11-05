import pytest
from sqlalchemy import Column, column, exists, func, literal_column, quoted_name, select, text
from sqlalchemy.orm import aliased
from sqlalchemy.sql.expression import true, union

from api.persistence.finance.models import ContractRow, InvoiceRow, PaymentRow
from api.persistence.ownership import OwnershipError
from api.persistence.query_guard import QueryGuard


@pytest.mark.parametrize(
    "statement",
    [
        pytest.param(select(InvoiceRow).order_by(InvoiceRow.due_date), id="order-by"),
        pytest.param(select(InvoiceRow).limit(1), id="limit"),
        pytest.param(select(InvoiceRow.status).distinct(), id="distinct-column"),
        pytest.param(select(func.count()).select_from(InvoiceRow), id="count"),
        pytest.param(select(InvoiceRow).where(InvoiceRow.status.in_(["PAID"])), id="in-list"),
        pytest.param(select(InvoiceRow).where(InvoiceRow.status.is_not(None)), id="is-not-null"),
    ],
)
def test_accepts_plain_navigation(statement: object) -> None:
    QueryGuard.reject_unsafe_constructs(statement)


@pytest.mark.parametrize(
    "statement",
    [
        pytest.param(select(InvoiceRow).where(text("1=1 OR 1=1")), id="text-in-where"),
        pytest.param(select(text("*")).select_from(text("finance.invoice")), id="text-in-from"),
        pytest.param(select(InvoiceRow).where(literal_column("1=1")), id="literal-column"),
        pytest.param(select(select(InvoiceRow).subquery()), id="subquery"),
        pytest.param(select(aliased(InvoiceRow)), id="alias"),
        pytest.param(select(select(InvoiceRow).cte()), id="cte"),
        pytest.param(
            select(InvoiceRow).where(InvoiceRow.contract_id.in_(select(ContractRow.id))),
            id="in-subquery",
        ),
        pytest.param(select(InvoiceRow).where(exists(select(ContractRow.id))), id="exists"),
        pytest.param(select(PaymentRow).join(InvoiceRow, text("true")), id="text-in-join"),
        pytest.param(select(PaymentRow).join(InvoiceRow, true()), id="true-in-join"),
        pytest.param(select(InvoiceRow).where(true()), id="true-in-where"),
        pytest.param(select(InvoiceRow).order_by(text("1")), id="text-in-order-by"),
        pytest.param(select(InvoiceRow).group_by(text("1")), id="text-in-group-by"),
        pytest.param(select(InvoiceRow).having(text("true")), id="text-in-having"),
        pytest.param(select(InvoiceRow.id.label("alias_name")), id="label"),
        pytest.param(select(func.count()).where(text("true")), id="count-with-text"),
        pytest.param(select(func.pg_catalog.count()), id="function-with-package"),
        pytest.param(
            select(InvoiceRow).where(Column(quoted_name("id = id OR true", quote=False))),
            id="raw-unattached-column",
        ),
        pytest.param(union(select(InvoiceRow), select(InvoiceRow)), id="union"),
        pytest.param(select(InvoiceRow).suffix_with("OR true"), id="suffix"),
        pytest.param(select(InvoiceRow).prefix_with("/* x */"), id="prefix"),
        pytest.param(select(InvoiceRow).with_statement_hint("OR true"), id="statement-hint"),
        pytest.param(select(InvoiceRow).with_hint(InvoiceRow, "OR true"), id="table-hint"),
        pytest.param(
            select(InvoiceRow).where(column(quoted_name("id = id OR true", quote=False))),
            id="raw-column",
        ),
        pytest.param(
            select(InvoiceRow).where(InvoiceRow.id.op("= 'x' OR true OR id =")("y")),
            id="custom-operator",
        ),
        pytest.param(
            select(func.query_to_xml("select 1 from finance.invoice")),
            id="sql-function",
        ),
    ],
)
def test_rejects_construct_that_escapes_the_adapter(statement: object) -> None:
    with pytest.raises(OwnershipError):
        QueryGuard.reject_unsafe_constructs(statement)
