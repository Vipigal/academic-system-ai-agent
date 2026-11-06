import pytest

from evals.oracle import QueryPreparer
from evals.oracle_queries import ORACLE_QUERIES
from evals.oracle_queries.scope import STUDENT_SCOPE


def test_named_parameters_become_positional_and_repeat_the_same_position() -> None:
    prepared = QueryPreparer.prepare(
        "agreement_remaining_due", "UniSaoPaulo:180696", {"agreement": "AG1", "position": "0"}
    )
    query = prepared.sql.removeprefix(STUDENT_SCOPE)
    assert prepared.arguments == ("UniSaoPaulo:180696", "AG1", "0")
    assert query.count("$2") == 1
    assert "OFFSET $3::text::int" in query
    assert ":" + "student" not in prepared.sql


def test_parameters_of_a_query_leave_out_the_student() -> None:
    assert QueryPreparer.parameters_of("debt_total") == frozenset()
    assert QueryPreparer.parameters_of("protocol_fee") == {"protocol"}


@pytest.mark.parametrize("name", sorted(ORACLE_QUERIES))
def test_every_query_reads_only_with_select(name: str) -> None:
    assert ORACLE_QUERIES[name].lstrip().upper().startswith("SELECT")
