import pytest

from api.persistence.core.source_enum import UnknownDialectValueError
from api.persistence.secretary.dialect import SecretaryDialect
from tests.integration.support.sql_oracle import SqlOracle

UNIT_PAIRS = """
    SELECT s.unit_name || '|' || u.unit_code
    FROM sag.unit s
    JOIN secretary.unit u
      ON split_part(u.unit_code, '-', 1) = CASE replace(s.brand, '_EAD', '')
             WHEN 'UniSaoPaulo' THEN 'SPA' WHEN 'UniMontanhas' THEN 'MON'
             WHEN 'UniLitoral' THEN 'LIT' WHEN 'UniAtlantico' THEN 'ATL'
             WHEN 'UniAraucaria' THEN 'ARA' END
     AND (u.unit_code LIKE '%-EAD') = (s.brand LIKE '%\\_EAD')
     AND lower(translate(u.city, 'ãáâéêíóôõúç', 'aaaeeiooouc'))
         = lower(translate(s.city, 'ãáâéêíóôõúç', 'aaaeeiooouc'))
     AND u.uf = s.uf
"""


async def test_every_academic_unit_translates_to_its_unit_in_the_secretary() -> None:
    pairs = (pair.split("|") for pair in await SqlOracle().values(UNIT_PAIRS))
    translated = dict(pairs)
    assert len(translated) == 27
    assert {name: SecretaryDialect.unit_code(name) for name in translated} == translated


def test_an_unknown_academic_unit_raises() -> None:
    with pytest.raises(UnknownDialectValueError):
        SecretaryDialect.unit_code("CAMPUS INEXISTENTE")
