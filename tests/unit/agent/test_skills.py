from datetime import date
from pathlib import Path

import pytest

from api.application.agent.skill_library import SKILL_FILE, SKILLS_ROOT, Skill, SkillLibrary
from api.application.agent.student_agent import StudentAgent
from api.application.agent.system_prompt import CURRENT_VERSION, SystemPrompt
from api.application.agent.tools.registry import ToolRegistry
from api.application.agent.tools.skill_tools import SkillTools
from api.domain.ontology.catalog import ONTOLOGIES
from api.domain.ontology.model import Area
from api.domain.ontology.renderer import OntologyRenderer
from tests.unit.agent.agent_support import (
    RecordingModel,
    answer,
    call,
    runtime_with,
    tool_results,
)

LIBRARY = SkillLibrary.load()
PROMPT = SystemPrompt.load()


@pytest.mark.parametrize("area", list(Area))
async def test_load_skill_returns_the_body_and_the_ontologies(area: Area) -> None:
    result = await SkillTools(LIBRARY).load_skill(area)

    assert result.data is not None
    assert OntologyRenderer.for_skill(area) in result.data
    assert result.data.startswith("# ")


@pytest.mark.parametrize("area", list(Area))
async def test_load_skill_hides_evidence_and_tables(area: Area) -> None:
    result = await SkillTools(LIBRARY).load_skill(area)

    assert result.data is not None
    for ontology in (item for item in ONTOLOGIES if item.area is area):
        assert ontology.evidence not in result.data
        for table in ontology.data:
            assert table not in result.data


def test_load_skill_passes_the_registry_rules() -> None:
    tool = ToolRegistry(SkillTools(LIBRARY)).tools[0]

    assert tool.definition.name == "load_skill"
    assert set(tool.definition.ontologies) == set(ONTOLOGIES)


async def test_the_agent_offers_load_skill_without_student_tools() -> None:
    model = RecordingModel(responses=[call("load_skill", {"area": "finance"}), answer()])

    run = await StudentAgent(runtime_with(model), (), "trace").run("Dúvida")

    assert tool_results(run.events)[0].status == "ok"
    assert "Financeiro" in str(tool_results(run.events)[0].complete["data"])


def test_each_area_has_a_skill_file_with_name_and_description() -> None:
    for area in Area:
        assert LIBRARY.instructions(area)
        assert f"`{area.value}`" in LIBRARY.listing()


def test_a_skill_without_frontmatter_fields_is_rejected() -> None:
    with pytest.raises(ValueError, match="finance"):
        Skill.parse(Area.FINANCE, "---\nname: lms\ndescription: x\n---\ncorpo")


def test_the_library_reads_the_files_once(tmp_path: Path) -> None:
    for area in Area:
        folder = tmp_path / area.value
        folder.mkdir()
        (folder / SKILL_FILE).write_text(
            f"---\nname: {area.value}\ndescription: d\n---\ncorpo {area.value}", encoding="utf-8"
        )

    library = SkillLibrary.load(tmp_path)
    fingerprint = library.fingerprint()
    (tmp_path / Area.FINANCE.value / SKILL_FILE).unlink()

    assert library.instructions(Area.FINANCE).startswith("corpo finance")
    assert library.fingerprint() == fingerprint
    assert fingerprint != LIBRARY.fingerprint()


def test_only_the_finance_skill_warns_about_credit_bureaus() -> None:
    bodies = {
        area: Skill.parse(
            area, (SKILLS_ROOT / area.value / SKILL_FILE).read_text(encoding="utf-8")
        ).body
        for area in Area
    }

    assert "Negativação" in bodies[Area.FINANCE]
    assert not [
        area
        for area, body in bodies.items()
        if area is not Area.FINANCE and "negativaç" in body.lower()
    ]


def test_the_prompt_is_versioned_and_lists_descriptions_without_ontologies() -> None:
    rendered = PROMPT.render(date(2026, 10, 31), LIBRARY.listing())

    assert PROMPT.version == CURRENT_VERSION
    assert "31/10/2026" in rendered
    for area in Area:
        assert f"`{area.value}`" in rendered
    assert not [item.key for item in ONTOLOGIES if item.definition in rendered]
    assert "{" not in rendered.replace("{}", "")


def test_a_prompt_version_is_read_from_its_own_file(tmp_path: Path) -> None:
    (tmp_path / "outra.md").write_text("Data {reference_date}. {skills}", encoding="utf-8")

    prompt = SystemPrompt.load("outra", tmp_path)

    assert prompt.version == "outra"
    assert prompt.render(date(2026, 1, 2), "lista") == "Data 02/01/2026. lista"
