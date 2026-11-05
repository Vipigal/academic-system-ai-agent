from sqlalchemy import text

from api.persistence.database import Database

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


class SqlOracle:
    def __init__(self, database: Database) -> None:
        self._database = database

    async def values(self, sql: str, **parameters: str) -> set[str]:
        async with self._database.db_session_factory() as db:
            result = await db.execute(text(sql), parameters)
            return {str(row[0]) for row in result}

    async def count(self, sql: str, **parameters: str) -> int:
        return int(next(iter(await self.values(sql, **parameters))))
