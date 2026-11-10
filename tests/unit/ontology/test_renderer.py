import pytest

from api.domain.ontology.model import Area, Ontology, Relation, RelationKind
from api.domain.ontology.renderer import OntologyRenderer

ORIGIN_CONCEPT = Ontology(
    key="origem",
    name="Origem visível",
    area=Area.FINANCE,
    synonyms=("sinônimo da origem",),
    definition="Definição da origem.",
    caveat="Aviso da origem.",
    never_say=("Frase proibida da origem",),
    relations=(
        Relation(
            RelationKind.NOT_IMPLIES,
            "destino",
            note="Nota da relação.",
        ),
    ),
)
TARGET_CONCEPT = Ontology(
    key="destino",
    name="Destino visível",
    area=Area.LMS,
    synonyms=("sinônimo do destino",),
    definition="Definição do destino.",
    caveat="Aviso do destino.",
    never_say=(),
)
OTHER_CONCEPT = Ontology(
    key="outro",
    name="Outro visível",
    area=Area.PROTOCOLS,
    synonyms=(),
    definition="Definição de outra área.",
    never_say=(),
)
SAMPLE = (ORIGIN_CONCEPT, TARGET_CONCEPT, OTHER_CONCEPT)


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


def test_lms_skill_shows_that_debt_does_not_imply_suspension() -> None:
    output = OntologyRenderer.for_skill(Area.LMS)

    assert "Dívida não implica Suspensão do AVA:" in output


def test_finance_skill_also_shows_that_debt_does_not_imply_suspension() -> None:
    assert "Dívida não implica Suspensão do AVA:" in OntologyRenderer.for_skill(Area.FINANCE)


def test_relation_with_both_ends_in_the_area_appears_once() -> None:
    output = OntologyRenderer.for_skill(Area.FINANCE)

    assert output.count("Dívida é composta de Multa e juros:") == 1
