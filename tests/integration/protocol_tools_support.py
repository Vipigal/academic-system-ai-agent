from api.application.dto.protocol_detail_dto import ProtocolDetailDto
from api.application.dto.protocol_dto import ProtocolDto
from api.application.dto.tool_result import ToolResult
from tests.integration.sql_oracle import SqlOracle

ONLINE_SAO_PAULO_PERSON = "3001888"
LITORAL_PERSON = "3002397"
ATLANTICO_PERSON = "3000896"
ARAUCARIA_ONLINE_PERSON = "3002324"
SAO_PAULO_PERSON = "3002552"
BOLETO_PERSON = "3003422"
LOCKED_PERSON = "3001432"
GUARDIAN_PERSON = "3003452"
UNPAID_FEE_PERSON = "3001324"
DUPLICATE_PERSON = "3032393"
TWO_ENROLLMENTS_PERSON = "3000071"
INTERNAL_NOTES_PERSON = "3000414"
DIPLOMA_PERSON = "3000357"
NO_FEE_INVOICE_PERSON = "3003870"
COUNT_STATEMENTS = (
    "SELECT count(*) FROM secretary.protocol",
    "SELECT count(*) FROM secretary.protocol_interaction",
    "SELECT count(*) FROM secretary.protocol_status_history",
    "SELECT count(*) FROM secretary.issued_document",
    "SELECT count(*) FROM finance.invoice",
    "SELECT count(*) FROM finance.payment",
)

COUNT_STATEMENTS = (
    "SELECT count(*) FROM secretary.protocol",
    "SELECT count(*) FROM secretary.protocol_interaction",
    "SELECT count(*) FROM secretary.protocol_status_history",
    "SELECT count(*) FROM secretary.issued_document",
    "SELECT count(*) FROM finance.invoice",
    "SELECT count(*) FROM finance.payment",
)


async def table_counts(oracle: SqlOracle) -> dict[str, int]:
    return {statement: await oracle.count(statement) for statement in COUNT_STATEMENTS}


def rows[T](result: ToolResult[list[T]]) -> list[T]:
    assert result.data is not None
    return result.data


def protocol_of(result: ToolResult[ProtocolDetailDto]) -> ProtocolDto:
    assert result.data is not None
    return result.data.protocol


def candidate_codes[T](result: ToolResult[T]) -> set[str]:
    return {candidate.code for candidate in result.candidates}
