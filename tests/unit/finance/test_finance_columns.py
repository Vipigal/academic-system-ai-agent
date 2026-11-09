from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine

from api.domain.finance.invoice import InvoiceKind
from api.persistence.finance.models import InvoiceRow

ASYNCPG = create_async_engine("postgresql+asyncpg://").dialect


def test_a_typed_column_binds_the_source_value_with_the_same_sql() -> None:
    statement = select(InvoiceRow.id).where(InvoiceRow.kind == InvoiceKind.SERVICE_FEE)
    compiled = statement.compile(dialect=ASYNCPG)
    assert "finance.invoice.invoicetype = $1::VARCHAR" in str(compiled)
    processor = InvoiceRow.kind.type.bind_processor(ASYNCPG)
    assert processor is not None
    assert processor(InvoiceKind.SERVICE_FEE) == "SERVICE_FEE"
