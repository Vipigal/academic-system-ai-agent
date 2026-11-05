from dataclasses import asdict, dataclass

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from api.domain.brand import Brand, EnrollmentRef, Modality
from api.persistence.database import Database
from api.persistence.identity_tables import PERSON_CPF, PROTOCOL_REQUESTER
from api.persistence.sag.dialect import SagDialect
from api.persistence.secretary.dialect import SecretaryDialect

OWN_CPF = "01234567890"
OTHER_CPF = "98765432100"
OWN_STUDENT_ID = "012345"
OTHER_STUDENT_ID = "055555"
OWN_ENROLLMENT = EnrollmentRef(Brand.SAO_PAULO, Modality.ONLINE, "01234")
OWN_UNIT = "SPA-SAO-EAD"
SYNTHETIC_SCHEMAS = {"schema_translate_map": {"secretary": "pg_temp", "sag": "pg_temp"}}
CREATE_PROTOCOL = text(
    "CREATE TEMP TABLE protocol (protocol text, stu_id text, requester_cpf text, "
    "requester_type text, unit_code text) ON COMMIT DROP",
)
CREATE_ENROLLMENT = text(
    "CREATE TEMP TABLE enrollment (brand text, student_id text, person_id text) ON COMMIT DROP",
)
INSERT_PROTOCOL = text(
    "INSERT INTO pg_temp.protocol VALUES (:protocol, :student, :cpf, :kind, :unit)",
)
INSERT_ENROLLMENT = text(
    "INSERT INTO pg_temp.enrollment VALUES ('UniSaoPaulo_EAD', :student, :student)",
)


@dataclass(frozen=True, slots=True)
class Requested:
    protocol: str
    student: str | None
    cpf: str
    kind: str
    unit: str = OWN_UNIT


VISIBLE = (
    Requested("student-with-id", OWN_STUDENT_ID, OWN_CPF, "Student"),
    Requested("alumni-with-id", OWN_STUDENT_ID, OWN_CPF, "Alumni"),
    Requested("id-without-leading-zero", "12345", OWN_CPF, "Student"),
    Requested("cpf-without-leading-zero", OWN_STUDENT_ID, "1234567890", "Student"),
    Requested("guardian-with-id", OWN_STUDENT_ID, OTHER_CPF, "Guardian"),
    Requested("student-without-id", None, OWN_CPF, "Student"),
    Requested("alumni-without-id", None, OWN_CPF, "Alumni"),
    Requested("typo-in-the-id", "999999", OWN_CPF, "Student"),
)
INVISIBLE = (
    Requested("third-party-without-id", None, OTHER_CPF, "Third Party"),
    Requested("third-party-with-the-own-cpf", None, OWN_CPF, "Third Party"),
    Requested("third-party-with-the-own-id", OWN_STUDENT_ID, OWN_CPF, "Third Party"),
    Requested("guardian-without-id", None, OTHER_CPF, "Guardian"),
    Requested("guardian-with-the-own-cpf-and-no-id", None, OWN_CPF, "Guardian"),
    Requested("own-id-asked-by-another-student", OWN_STUDENT_ID, OTHER_CPF, "Student"),
    Requested("own-cpf-with-the-id-of-another-student", OTHER_STUDENT_ID, OWN_CPF, "Student"),
    Requested("own-id-in-another-brand", OWN_STUDENT_ID, OTHER_CPF, "Guardian", "MON-BHZ-EAD"),
    Requested("own-id-in-another-modality", OWN_STUDENT_ID, OTHER_CPF, "Guardian", "SPA-PAU"),
    Requested("own-cpf-in-another-brand", None, OWN_CPF, "Student", "MON-BHZ-EAD"),
    Requested("own-cpf-in-another-modality", None, OWN_CPF, "Student", "SPA-PAU"),
)


async def create_synthetic_tables(db: AsyncSession) -> None:
    await db.execute(CREATE_PROTOCOL)
    await db.execute(CREATE_ENROLLMENT)
    for student in (OWN_STUDENT_ID, OTHER_STUDENT_ID):
        await db.execute(INSERT_ENROLLMENT, {"student": student})
    for requested in (*VISIBLE, *INVISIBLE):
        await db.execute(INSERT_PROTOCOL, asdict(requested))


async def test_cascade_shows_only_what_is_proven_to_be_of_the_person(database: Database) -> None:
    clause = SecretaryDialect.protocol_of(OWN_CPF, {OWN_ENROLLMENT: OWN_STUDENT_ID})
    async with database.db_session_factory() as db:
        await create_synthetic_tables(db)
        resolved = await db.scalars(
            select(PROTOCOL_REQUESTER.c.protocol).where(clause),
            execution_options=SYNTHETIC_SCHEMAS,
        )
        assert set(resolved.all()) == {requested.protocol for requested in VISIBLE}


async def test_empty_identity_resolves_nothing(database: Database) -> None:
    clause = SecretaryDialect.protocol_of("", {})
    async with database.db_session_factory() as db:
        resolved = await db.scalars(select(PROTOCOL_REQUESTER.c.protocol).where(clause))
        assert resolved.all() == []


async def test_empty_cpf_matches_no_person_even_with_blank_cpfs(database: Database) -> None:
    async with database.db_session_factory() as db:
        await db.execute(text("CREATE TEMP TABLE person (person_id text, cpf text) ON COMMIT DROP"))
        await db.execute(
            text("INSERT INTO pg_temp.person VALUES ('blank', ''), ('null', NULL), ('dots', '.-')")
        )
        resolved = await db.scalars(
            select(PERSON_CPF.c.person_id).where(SagDialect.person_with_cpf("")),
            execution_options=SYNTHETIC_SCHEMAS,
        )
        assert resolved.all() == []
