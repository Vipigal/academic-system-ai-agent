from pathlib import Path
from types import TracebackType
from typing import Self

from sqlalchemy.ext.asyncio import AsyncConnection, AsyncEngine, create_async_engine
from sqlalchemy.pool import NullPool

from evals.dataset.oracle_settings import OracleSettings

FOREIGN_IDENTIFIERS = r"""
WITH own_cpf AS (
    SELECT regexp_replace(person.cpf, '\D', '', 'g') AS cpf
    FROM sag.enrollment JOIN sag.person USING (person_id)
    WHERE enrollment.brand || ':' || enrollment.student_id = $1
),
student_enrollment AS (
    SELECT enrollment.* FROM sag.enrollment
    WHERE enrollment.brand || ':' || enrollment.student_id = $1
),
own_enrollments AS (
    SELECT enrollment.*
    FROM sag.enrollment JOIN sag.person USING (person_id)
    WHERE regexp_replace(person.cpf, '\D', '', 'g') = (SELECT cpf FROM own_cpf)
),
own_contracts AS (
    SELECT contract.*
    FROM finance.contract
    JOIN own_enrollments enrollment
      ON contract.companycode = CASE split_part(enrollment.brand, '_', 1)
             WHEN 'UniSaoPaulo' THEN '1010'
             WHEN 'UniMontanhas' THEN '1020'
             WHEN 'UniLitoral' THEN '1030'
             WHEN 'UniAtlantico' THEN '1040'
             WHEN 'UniAraucaria' THEN '1050'
         END
     AND contract.businessarea
         = CASE WHEN enrollment.brand LIKE '%\_EAD' THEN 'DIGITAL' ELSE 'PRESENCIAL' END
     AND lpad(split_part(trim(contract.academicref), '-', 1), 5, '0')
         = left(enrollment.student_id, 5)
),
own_invoices AS (
    SELECT invoice.* FROM finance.invoice
    WHERE invoice.contractid IN (SELECT contractid FROM own_contracts)
),
own_protocols AS (
    SELECT DISTINCT protocol.*
    FROM secretary.protocol
    JOIN secretary.unit ON unit.unit_code = protocol.unit_code
    JOIN own_enrollments enrollment
      ON enrollment.brand = replace(translate(unit.brand_name, 'ãáâ', 'aaa'), ' ', '')
         || CASE unit.unit_type WHEN 'Polo EAD' THEN '_EAD' ELSE '' END
    WHERE (enrollment.student_id = lpad(protocol.stu_id, 6, '0')
           AND (protocol.requester_type = 'Guardian'
                OR (protocol.requester_type IN ('Student', 'Alumni')
                    AND lpad(protocol.requester_cpf, 11, '0') = (SELECT cpf FROM own_cpf))))
       OR (protocol.requester_type IN ('Student', 'Alumni')
           AND lpad(protocol.requester_cpf, 11, '0') = (SELECT cpf FROM own_cpf)
           AND NOT EXISTS (SELECT 1 FROM sag.enrollment other
                           WHERE other.student_id = lpad(protocol.stu_id, 6, '0')))
),
own_accounts AS (
    SELECT account.*
    FROM lms.mdl_user account
    JOIN lms.mdl_tenant tenant ON tenant.id = account.tenant_id
    JOIN own_enrollments enrollment
      ON lower(split_part(enrollment.brand, '_', 1)) = tenant.slug
     AND (enrollment.brand LIKE '%\_EAD') = (upper(trim(account.student_id)) LIKE 'EAD\_%')
     AND left(enrollment.student_id, 5) = split_part(trim(account.student_id), '_', 2)
)
        SELECT invoiceid::text FROM finance.invoice
        UNION SELECT documentnumber::text FROM finance.invoice
        UNION SELECT paymentid::text FROM finance.payment
        UNION SELECT contractid::text FROM finance.contract
        UNION SELECT agreementid::text FROM finance.agreement
        UNION SELECT protocol::text FROM secretary.protocol
        UNION SELECT brand || ':' || student_id FROM sag.enrollment
        UNION SELECT student_id FROM sag.enrollment
        UNION SELECT student_lms_id::text FROM lms.mdl_user WHERE student_id IS NOT NULL
        UNION SELECT unnest(ARRAY[full_name, email, regexp_replace(cpf, '\D', '', 'g')])
        FROM sag.person
        EXCEPT (
            SELECT invoiceid::text FROM own_invoices
            UNION SELECT documentnumber::text FROM own_invoices
            UNION SELECT paymentid::text FROM finance.payment
            WHERE invoiceid IN (SELECT invoiceid FROM own_invoices)
            UNION SELECT contractid::text FROM own_contracts
            UNION SELECT agreementid::text FROM finance.agreement
            WHERE contractid IN (SELECT contractid FROM own_contracts)
            UNION SELECT protocol::text FROM own_protocols
            UNION SELECT brand || ':' || student_id FROM own_enrollments
            UNION SELECT student_id FROM own_enrollments
            UNION SELECT student_lms_id::text FROM own_accounts
            UNION SELECT unnest(ARRAY[full_name, email, regexp_replace(cpf, '\D', '', 'g')])
            FROM sag.person
            WHERE regexp_replace(cpf, '\D', '', 'g') = (SELECT cpf FROM own_cpf)
        )
"""


class Oracle:
    def __init__(self, database_url: str) -> None:
        self._engine: AsyncEngine = create_async_engine(database_url, poolclass=NullPool)
        self._connection: AsyncConnection | None = None

    @classmethod
    def from_environment(cls, env_file: Path | None = None) -> Self:
        settings = OracleSettings.from_environment(env_file)
        return cls(settings.oracle_database_url.get_secret_value())

    async def __aenter__(self) -> Self:
        self._connection = await self._engine.connect()
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        if self._connection is not None:
            await self._connection.close()
        await self._engine.dispose()

    async def foreign_identifiers(self, student: str) -> frozenset[str]:
        if self._connection is None:
            raise RuntimeError("Abra o oráculo com async with antes de consultar")
        result = await self._connection.exec_driver_sql(FOREIGN_IDENTIFIERS, (student,))
        values = (row[0] for row in result)
        return frozenset(str(value) for value in values if value is not None)
