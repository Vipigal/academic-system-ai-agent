from functools import cache

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine
from sqlalchemy.pool import NullPool

PROTOCOL_OWNERS = r"""
    SELECT protocol.protocol || ':' || regexp_replace(person.cpf, '\D', '', 'g')
    FROM secretary.protocol
    JOIN secretary.unit ON unit.unit_code = protocol.unit_code
    JOIN sag.enrollment
      ON enrollment.brand = replace(translate(unit.brand_name, 'ãáâ', 'aaa'), ' ', '')
         || CASE unit.unit_type WHEN 'Polo EAD' THEN '_EAD' ELSE '' END
    JOIN sag.person ON person.person_id = enrollment.person_id
    WHERE (enrollment.student_id = lpad(protocol.stu_id, 6, '0')
           AND (protocol.requester_type = 'Guardian'
                OR (protocol.requester_type IN ('Student', 'Alumni')
                    AND regexp_replace(person.cpf, '\D', '', 'g')
                        = lpad(protocol.requester_cpf, 11, '0'))))
       OR (protocol.requester_type IN ('Student', 'Alumni')
           AND regexp_replace(person.cpf, '\D', '', 'g') = lpad(protocol.requester_cpf, 11, '0')
           AND NOT EXISTS (SELECT 1 FROM sag.enrollment other
                           WHERE other.student_id = lpad(protocol.stu_id, 6, '0')))
"""

LMS_OWNERS = r"""
    SELECT account.student_lms_id || ':' || regexp_replace(person.cpf, '\D', '', 'g')
    FROM lms.mdl_user account
    JOIN lms.mdl_tenant tenant ON tenant.id = account.tenant_id
    JOIN sag.enrollment
      ON lower(split_part(enrollment.brand, '_', 1)) = tenant.slug
     AND (enrollment.brand LIKE '%\_EAD') = (upper(trim(account.student_id)) LIKE 'EAD\_%')
     AND left(enrollment.student_id, 5) = split_part(trim(account.student_id), '_', 2)
    JOIN sag.person ON person.person_id = enrollment.person_id
"""


class OracleSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="APP_")

    oracle_database_url: SecretStr


def admin_url() -> str:
    return OracleSettings.model_validate({}).oracle_database_url.get_secret_value()


@cache
def admin_engine() -> AsyncEngine:
    return create_async_engine(admin_url(), poolclass=NullPool)


class SqlOracle:
    async def values(self, sql: str, **parameters: str) -> set[str]:
        async with admin_engine().connect() as connection:
            result = await connection.execute(text(sql), parameters)
            return {str(row[0]) for row in result}

    async def owned_by_cpf(self, sql: str, cpf: str) -> set[str]:
        pairs = (pair.rsplit(":", 1) for pair in await self.values(sql))
        return {identifier for identifier, owner in pairs if owner == cpf}

    async def count(self, sql: str, **parameters: str) -> int:
        return int(next(iter(await self.values(sql, **parameters))))
