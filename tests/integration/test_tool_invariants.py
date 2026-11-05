import asyncio
from collections.abc import AsyncIterator, Iterator

import pytest
import pytest_asyncio

from api.composition.student_tools_factory import StudentToolsFactory
from api.domain.ontology.catalog import ONTOLOGIES
from api.persistence.database import Database
from api.presentation.tools.registry import ALLOWED_PARAMETERS, ToolRegistry
from api.settings import ReferenceClock, Settings
from tests.integration import invariant_json, invariant_queries, invariant_sample, invariant_support
from tests.integration.sql_oracle import PROTOCOL_OWNERS, SqlOracle

type Person = invariant_sample.SampledPerson
type Leak = tuple[str, str, object, set[str]]
type Answers = dict[tuple[str, str, object], invariant_json.Output]
UNKNOWN_PERSON = "does-not-exist"
TOOL_COUNT = 19
PAGINATED_TOOLS = frozenset(
    {
        "list_course_offers",
        "get_curriculum",
        "list_subject_records",
        "list_invoices",
        "list_payments",
        "list_protocols",
        "list_online_exams",
        "list_material_views",
    }
)
IDENTIFIER_TOOLS = frozenset(
    {
        "get_curriculum",
        "list_subject_records",
        "list_subject_professors",
        "list_online_exams",
        "list_material_views",
        "get_protocol",
        "propose_protocol",
    }
)
FINANCE_LISTS = {
    "list_invoices": invariant_queries.OWN_INVOICES,
    "list_payments": invariant_queries.OWN_CONFIRMED_PAYMENTS,
}
EMPTY_VALUES = frozenset({"", "None"})
MISSING = invariant_support.MISSING
JsonLeaves = invariant_json.JsonLeaves
Exposure = invariant_json.Exposure


def production_factory(database: Database) -> StudentToolsFactory:
    return StudentToolsFactory(database, ReferenceClock(Settings.from_environment()))


@pytest_asyncio.fixture(scope="module", loop_scope="module")
async def sample() -> AsyncIterator[list[Person]]:
    connected = Database(Settings.from_environment().database_url.get_secret_value())
    builder = invariant_sample.SampleBuilder(connected, production_factory(connected))
    people = sorted(await SqlOracle(connected).values(invariant_queries.SAMPLE_PEOPLE))
    yield list(await asyncio.gather(*(builder.person(person_id) for person_id in people)))
    await connected.dispose()


@pytest.fixture
async def registry(database: Database) -> ToolRegistry:
    return await production_factory(database).for_person(UNKNOWN_PERSON)


@pytest.fixture
def oracle(database: Database) -> SqlOracle:
    return SqlOracle(database)


def all_calls(sample: list[Person]) -> Iterator[invariant_json.ToolCall]:
    return (call for person in sample for call in person.calls)


def walked(person: Person, tool: str) -> list[invariant_json.Output]:
    return [item for page in person.walks[tool].small for item in page.get("data") or []]


def large_items(person: Person, tool: str) -> list[invariant_json.Output]:
    return [item for page in person.walks[tool].large for item in page.get("data") or []]


def joined_refs(person: Person) -> str:
    return invariant_support.joined(invariant_support.enrollment_refs(person.session))


async def test_sample_covers_brands_modalities_two_enrollments_and_guardians(
    sample: list[Person], oracle: SqlOracle
) -> None:
    guardian = await oracle.values(invariant_queries.GUARDIAN_PROTOCOLS)
    brands = {brand for person in sample for brand, _ in person.session.enrollment_keys}
    assert 5 <= len(sample) <= 10
    assert len({brand.split("_")[0] for brand in brands}) == 5
    assert {brand.endswith("_EAD") for brand in brands} == {True, False}
    assert any(len(person.session.enrollment_keys) > 1 for person in sample)
    assert any(person.session.protocol_ids & guardian for person in sample)


def test_no_tool_receives_identity(registry: ToolRegistry) -> None:
    received = {
        name for tool in registry.tools for name in invariant_support.Sweep.parameters_of(tool)
    }
    assert received <= ALLOWED_PARAMETERS


def test_every_registered_tool_has_description_and_ontology(registry: ToolRegistry) -> None:
    assert len(registry.tools) == TOOL_COUNT
    assert all(tool.definition.description for tool in registry.tools)
    assert all(tool.definition.ontologies for tool in registry.tools)


def test_the_sweep_calls_every_tool_for_every_person(sample: list[Person]) -> None:
    assert all(len({call.tool for call in person.calls}) == TOOL_COUNT for person in sample)


async def foreign_identifiers(oracle: SqlOracle, person: Person) -> set[str]:
    session = person.session
    return await oracle.values(
        invariant_queries.FOREIGN_IDENTIFIERS,
        contracts=invariant_support.joined(session.contract_ids),
        protocols=invariant_support.joined(session.protocol_ids),
        enrollments=joined_refs(person),
        accounts=invariant_support.joined(session.lms_user_ids),
    )


async def test_compromised_agent_gets_no_identifier_of_other_people(
    sample: list[Person], oracle: SqlOracle
) -> None:
    leaks: list[Leak] = []
    for person in sample:
        foreign = await foreign_identifiers(oracle, person)
        leaks.extend(
            (person.person_id, call.tool, call.arguments, leaked)
            for call in person.calls
            if (leaked := set(JsonLeaves.strings(call.output)) & foreign)
        )
    assert leaks == []


async def test_the_leak_check_sees_the_own_identifiers(
    sample: list[Person], oracle: SqlOracle
) -> None:
    seen = {text for call in all_calls(sample) for text in JsonLeaves.strings(call.output)}
    for person in sample:
        contracts = invariant_support.joined(person.session.contract_ids)
        invoices = await oracle.values(invariant_queries.OWN_INVOICES, contracts=contracts)
        own = (invoices, person.session.contract_ids, joined_refs(person).split(","))
        assert all(set(identifiers) & seen for identifiers in own if identifiers)
    assert any(person.session.protocol_ids & seen for person in sample)


def answers_of(person: Person) -> Answers:
    return {
        (call.tool, call.varied, call.arguments[call.varied]): call.output
        for call in person.calls
        if call.varied in MISSING
    }


def foreign_answers(person: Person) -> Iterator[tuple[str, str, object]]:
    for tool, name, value in answers_of(person):
        if value in person.pool.foreign[name]:
            yield tool, name, value


def test_identifier_of_another_person_gets_the_same_answer_as_a_missing_one(
    sample: list[Person],
) -> None:
    differences = [
        (person.person_id, tool, name, value)
        for person in sample
        for tool, name, value in foreign_answers(person)
        if answers_of(person)[tool, name, value] != answers_of(person)[tool, name, MISSING[name]]
    ]
    compared = {tool for person in sample for tool, _, _ in foreign_answers(person)}
    assert compared == IDENTIFIER_TOOLS
    assert differences == []


async def test_no_cpf_internal_note_analyst_payer_or_collection_stage_appears(
    sample: list[Person], oracle: SqlOracle
) -> None:
    forbidden = await oracle.values(invariant_queries.CPFS)
    forbidden |= await oracle.values(invariant_queries.FORBIDDEN_VALUES)
    notes = await oracle.values(invariant_queries.INTERNAL_NOTES)
    exposed = [
        (call.tool, call.arguments, found)
        for call in all_calls(sample)
        if (
            found := Exposure.keys(call.output)
            | Exposure.values(call.output, forbidden - EMPTY_VALUES)
            | Exposure.texts(call.output, notes)
        )
    ]
    assert notes
    assert exposed == []


def test_no_ontology_evidence_or_data_reaches_a_tool_result(sample: list[Person]) -> None:
    hidden = {ontology.evidence for ontology in ONTOLOGIES}
    hidden |= {table for ontology in ONTOLOGIES for table in ontology.data}
    hidden |= {
        relation.evidence
        for ontology in ONTOLOGIES
        for relation in ontology.relations
        if relation.evidence
    }
    dumped = "\n".join(JsonLeaves.text(call.output) for call in all_calls(sample))
    assert {text for text in hidden if text in dumped} == set()


def totals_of(person: Person, tool: str) -> set[str]:
    walk = person.walks[tool]
    return {str(page.get("totals")) for page in walk.small + walk.large}


def test_small_pages_walk_to_the_full_list_with_stable_totals(sample: list[Person]) -> None:
    broken = [
        (person.person_id, tool)
        for person in sample
        for tool in person.walks
        if walked(person, tool) != large_items(person, tool) or len(totals_of(person, tool)) != 1
    ]
    assert all(set(person.walks) == PAGINATED_TOOLS for person in sample)
    assert any(len(walk.small) > 2 for person in sample for walk in person.walks.values())
    assert broken == []


@pytest.mark.parametrize(("tool", "sql"), FINANCE_LISTS.items())
async def test_walked_finance_lists_match_the_oracle(
    sample: list[Person], oracle: SqlOracle, tool: str, sql: str
) -> None:
    for person in sample:
        contracts = invariant_support.joined(person.session.contract_ids)
        expected = await oracle.values(sql, contracts=contracts)
        assert sorted(item["id"] for item in walked(person, tool)) == sorted(expected)


async def test_walked_protocols_match_the_oracle(sample: list[Person], oracle: SqlOracle) -> None:
    owners = [pair.split(":") for pair in await oracle.values(PROTOCOL_OWNERS)]
    for person in sample:
        numbers = sorted(item["number"] for item in walked(person, "list_protocols"))
        assert numbers == sorted(protocol for protocol, cpf in owners if cpf == person.session.cpf)


async def test_walked_subject_records_match_the_oracle(
    sample: list[Person], oracle: SqlOracle
) -> None:
    for person in sample:
        records = walked(person, "list_subject_records")
        found = ["/".join((item["enrollment"], item["class_id"])) for item in records]
        expected = await oracle.values(
            invariant_queries.OWN_RECORDS, enrollments=joined_refs(person)
        )
        assert sorted(found) == sorted(expected)
