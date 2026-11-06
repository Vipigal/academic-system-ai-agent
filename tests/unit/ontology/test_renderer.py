import re
from collections.abc import Iterator

import pytest

from api.domain.ontology.catalog import ONTOLOGIES
from api.domain.ontology.model import Area, Ontology, Origin, Relation, RelationKind, System
from api.domain.ontology.renderer import OntologyRenderer

HIDDEN_EVIDENCE = "EVIDENCIA_DO_CONCEITO"
HIDDEN_RELATION_EVIDENCE = "EVIDENCIA_DA_RELACAO"
HIDDEN_TABLE = "schema.tabela_secreta"
MEASURE_PATTERN = re.compile(r"\d[\d.]*/\d[\d.]*")

ORIGIN_CONCEPT = Ontology(
    key="origem",
    name="Origem visível",
    area=Area.FINANCE,
    synonyms=("sinônimo da origem",),
    definition="Definição da origem.",
    source=System.FINANCE,
    origin=Origin.INFERRED,
    evidence=HIDDEN_EVIDENCE,
    data=(HIDDEN_TABLE,),
    caveat="Aviso da origem.",
    never_say=("Frase proibida da origem",),
    relations=(
        Relation(
            RelationKind.NOT_IMPLIES,
            "destino",
            note="Nota da relação.",
            evidence=HIDDEN_RELATION_EVIDENCE,
        ),
    ),
)
TARGET_CONCEPT = Ontology(
    key="destino",
    name="Destino visível",
    area=Area.LMS,
    synonyms=("sinônimo do destino",),
    definition="Definição do destino.",
    source=None,
    origin=Origin.ABSENT,
    evidence=HIDDEN_EVIDENCE,
    data=(HIDDEN_TABLE,),
    caveat="Aviso do destino.",
    never_say=(),
)
OTHER_CONCEPT = Ontology(
    key="outro",
    name="Outro visível",
    area=Area.PROTOCOLS,
    synonyms=(),
    definition="Definição de outra área.",
    source=System.SECRETARY,
    origin=Origin.CONFIRMED,
    evidence=HIDDEN_EVIDENCE,
    data=(),
    never_say=(),
)
SAMPLE = (ORIGIN_CONCEPT, TARGET_CONCEPT, OTHER_CONCEPT)


def hidden_texts() -> Iterator[str]:
    for ontology in ONTOLOGIES:
        yield ontology.evidence
        yield from ontology.data
        yield from (relation.evidence for relation in ontology.relations if relation.evidence)


@pytest.mark.parametrize(
    "expected",
    [
        "### Origem visível (`origem`)",
        "sinônimo da origem",
        "Definição da origem.",
        "Aviso da origem.",
        "Frase proibida da origem",
    ],
)
def test_skill_shows_what_the_model_needs(expected: str) -> None:
    assert expected in OntologyRenderer.for_skill(Area.FINANCE, SAMPLE)


def test_skill_shows_relation_when_concept_is_the_origin() -> None:
    output = OntologyRenderer.for_skill(Area.FINANCE, SAMPLE)

    assert "Origem visível não implica Destino visível: Nota da relação." in output


def test_skill_shows_relation_when_concept_is_the_target() -> None:
    output = OntologyRenderer.for_skill(Area.LMS, SAMPLE)

    assert "Origem visível não implica Destino visível: Nota da relação." in output


def test_skill_leaves_out_other_areas() -> None:
    output = OntologyRenderer.for_skill(Area.FINANCE, SAMPLE)

    assert "Definição de outra área." not in output
    assert "Definição do destino." not in output


def test_skill_of_unrelated_area_has_no_relation() -> None:
    assert "não implica" not in OntologyRenderer.for_skill(Area.PROTOCOLS, SAMPLE)


@pytest.mark.parametrize("area", [Area.FINANCE, Area.LMS, Area.PROTOCOLS])
@pytest.mark.parametrize("hidden", [HIDDEN_EVIDENCE, HIDDEN_RELATION_EVIDENCE, HIDDEN_TABLE])
def test_skill_never_carries_evidence_or_data(area: Area, hidden: str) -> None:
    assert hidden not in OntologyRenderer.for_skill(area, SAMPLE)


@pytest.mark.parametrize("area", list(Area))
def test_real_skill_never_carries_evidence_or_data(area: Area) -> None:
    output = OntologyRenderer.for_skill(area)

    assert [text for text in hidden_texts() if text in output] == []


@pytest.mark.parametrize("area", list(Area))
def test_real_skill_carries_no_measured_ratio(area: Area) -> None:
    assert MEASURE_PATTERN.findall(OntologyRenderer.for_skill(area)) == []


@pytest.mark.parametrize("area", list(Area))
def test_real_skill_carries_no_table_name(area: Area) -> None:
    output = OntologyRenderer.for_skill(area)

    assert re.findall(r"\b(?:sag|finance|secretary|lms)\.\w+", output) == []


def test_lms_skill_shows_that_debt_does_not_imply_suspension() -> None:
    output = OntologyRenderer.for_skill(Area.LMS)

    assert "Dívida não implica Suspensão do AVA:" in output


def test_finance_skill_also_shows_that_debt_does_not_imply_suspension() -> None:
    assert "Dívida não implica Suspensão do AVA:" in OntologyRenderer.for_skill(Area.FINANCE)


def test_relation_with_both_ends_in_the_area_appears_once() -> None:
    output = OntologyRenderer.for_skill(Area.FINANCE)

    assert output.count("Dívida é composta de Multa e juros:") == 1


@pytest.mark.parametrize(
    "expected",
    [
        "`origem`",
        "Origem visível",
        "sinônimo da origem",
        "Definição da origem.",
        "`INFERRED`",
        HIDDEN_EVIDENCE,
        HIDDEN_RELATION_EVIDENCE,
        HIDDEN_TABLE,
        "Aviso da origem.",
        "Frase proibida da origem",
        "Nota da relação.",
        "`destino`",
    ],
)
def test_document_carries_everything(expected: str) -> None:
    assert expected in OntologyRenderer.for_document(SAMPLE)


def test_document_names_the_official_system() -> None:
    assert "**Sistema:** Financeiro" in OntologyRenderer.for_document(SAMPLE)


def test_document_marks_concept_without_system() -> None:
    assert "**Sistema:** nenhum" in OntologyRenderer.for_document(SAMPLE)


def test_real_document_has_every_concept() -> None:
    output = OntologyRenderer.for_document()

    assert [item.key for item in ONTOLOGIES if f"`{item.key}`" not in output] == []


def test_real_document_has_every_hidden_text() -> None:
    output = OntologyRenderer.for_document()

    assert [text for text in hidden_texts() if text not in output] == []
