import pytest

from evals.golden.__main__ import GoldenCli
from evals.oracle import Oracle
from tests.integration.support.sql_oracle import PROTOCOL_OWNERS, SqlOracle

CPF_OF = r"""
    SELECT regexp_replace(person.cpf, '\D', '', 'g') FROM sag.enrollment
    JOIN sag.person USING (person_id)
    WHERE enrollment.brand || ':' || enrollment.student_id = :student
"""


async def test_the_validator_runs_every_query_and_passes() -> None:
    report = await GoldenCli.check()
    lines = list(report.lines())
    assert report.passed, "\n".join(line for line in lines if ": " in line and "=" not in line)
    assert lines[0] == "Itens: 60 perguntas, 30 ataques"
    assert lines[-1] == "OK"


@pytest.mark.parametrize(
    "student",
    [
        pytest.param("UniSaoPaulo:182460", id="guardian"),
        pytest.param("UniLitoral:120561", id="without-student-id"),
        pytest.param("UniSaoPaulo_EAD:012831", id="online"),
        pytest.param("UniAraucaria:090557", id="single-protocol"),
    ],
)
async def test_protocol_owners_match_the_test_oracle(student: str) -> None:
    oracle = SqlOracle()
    cpf = next(iter(await oracle.values(CPF_OF, student=student)))
    expected = await oracle.owned_by_cpf(PROTOCOL_OWNERS, cpf)
    async with Oracle.from_environment() as eval_oracle:
        found = await eval_oracle.rows("protocols_of_student", student, {})
    assert set((found[0] or "").split(",")) == expected
