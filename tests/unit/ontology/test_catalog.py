from dataclasses import replace

import pytest

from api.domain.ontology.catalog import ONTOLOGIES
from api.domain.ontology.model import Area, Ontology, Origin, Relation, RelationKind, System
from api.domain.ontology.validator import OntologyValidator

KEYS_BY_AREA = {
    Area.ACADEMIC_ENROLLMENT: {
        "matricula",
        "rematricula",
        "trancamento",
        "matriz",
        "pre_requisito",
        "oferta",
        "tcc_e_estagio",
        "projeto_integrador",
        "data_de_referencia",
        "regras_de_trancamento",
        "calendario_2027",
        "impedimento_por_pre_requisito",
    },
    Area.ACADEMIC_PERFORMANCE: {
        "resultado",
        "av",
        "media",
        "criterio_de_aprovacao",
        "frequencia",
        "cr",
        "conclusao",
        "registro_oficial",
        "sala_e_horario",
        "bloqueio_de_diploma",
    },
    Area.FINANCE: {
        "divida",
        "multa_e_juros",
        "proximo_boleto",
        "pagamento",
        "estorno",
        "bolsa",
        "mensalidade",
        "parcela_de_acordo",
        "acordo",
        "quitacao",
        "pagador",
        "cobranca",
        "criterios_de_bolsa",
        "negativacao",
    },
    Area.PROTOCOLS: {
        "protocolo",
        "servico",
        "prazo_de_atendimento",
        "taxa_de_servico",
        "documento_emitido",
        "pedido_de_terceiro",
    },
    Area.LMS: {
        "prova_online",
        "nota_do_ava",
        "visualizacao_de_material",
        "tentativa",
        "ultimo_acesso",
        "gabarito",
        "suspensao_do_ava",
    },
    Area.OVERVIEW: {"periodo_coberto", "pendencia"},
    Area.LIMITS: {"outros_alunos", "dados_internos", "identidade"},
}
KEYS_BY_ORIGIN = {
    Origin.INFERRED: {
        "av",
        "media",
        "criterio_de_aprovacao",
        "frequencia",
        "tentativa",
        "ultimo_acesso",
    },
    Origin.POLICY: {
        "data_de_referencia",
        "registro_oficial",
        "pagador",
        "cobranca",
        "pedido_de_terceiro",
        "pendencia",
        "outros_alunos",
        "dados_internos",
        "identidade",
    },
    Origin.ABSENT: {
        "sala_e_horario",
        "regras_de_trancamento",
        "criterios_de_bolsa",
        "calendario_2027",
        "gabarito",
        "negativacao",
        "bloqueio_de_diploma",
        "suspensao_do_ava",
        "impedimento_por_pre_requisito",
    },
}
RELATIONS = {
    (RelationKind.COMPOSED_OF, "divida", "multa_e_juros"),
    (RelationKind.COMPOSED_OF, "mensalidade", "bolsa"),
    (RelationKind.LEADS_TO, "servico", "taxa_de_servico"),
    (RelationKind.LEADS_TO, "servico", "acordo"),
    (RelationKind.LEADS_TO, "acordo", "parcela_de_acordo"),
    (RelationKind.NOT_IMPLIES, "divida", "bloqueio_de_diploma"),
    (RelationKind.NOT_IMPLIES, "divida", "suspensao_do_ava"),
    (RelationKind.NOT_IMPLIES, "pre_requisito", "impedimento_por_pre_requisito"),
    (RelationKind.NOT_IMPLIES, "protocolo", "taxa_de_servico"),
    (RelationKind.NOT_IMPLIES, "trancamento", "quitacao"),
    (RelationKind.NOT_IMPLIES, "matricula", "quitacao"),
    (RelationKind.NOT_IMPLIES, "cobranca", "negativacao"),
    (RelationKind.NOT_SAME_AS, "nota_do_ava", "registro_oficial"),
    (RelationKind.NOT_SAME_AS, "parcela_de_acordo", "mensalidade"),
    (RelationKind.NOT_SAME_AS, "tcc_e_estagio", "projeto_integrador"),
    (RelationKind.NOT_SAME_AS, "estorno", "pagamento"),
    (RelationKind.NOT_SAME_AS, "prazo_de_atendimento", "regras_de_trancamento"),
}


def concept(key: str, *relations: Relation) -> Ontology:
    return Ontology(
        key=key,
        name=key,
        area=Area.FINANCE,
        synonyms=(),
        definition="definição",
        source=System.FINANCE,
        origin=Origin.CONFIRMED,
        evidence="evidência",
        data=(),
        never_say=(),
        relations=relations,
    )


def test_catalog_is_valid() -> None:
    assert OntologyValidator.errors(ONTOLOGIES) == []


@pytest.mark.parametrize("area", list(Area))
def test_each_area_has_the_keys_of_the_spec(area: Area) -> None:
    keys = {ontology.key for ontology in ONTOLOGIES if ontology.area is area}

    assert keys == KEYS_BY_AREA[area]


@pytest.mark.parametrize("origin", list(KEYS_BY_ORIGIN))
def test_each_origin_has_the_keys_of_the_spec(origin: Origin) -> None:
    keys = {ontology.key for ontology in ONTOLOGIES if ontology.origin is origin}

    assert keys == KEYS_BY_ORIGIN[origin]


def test_catalog_has_54_concepts() -> None:
    assert len(ONTOLOGIES) == 54


def test_catalog_declares_exactly_the_relations_of_the_spec() -> None:
    declared = [
        (relation.kind, ontology.key, relation.target)
        for ontology in ONTOLOGIES
        for relation in ontology.relations
    ]

    assert len(declared) == len(RELATIONS)
    assert set(declared) == RELATIONS


def test_validator_accepts_a_consistent_set() -> None:
    target = concept("destino")
    origin = concept("origem", Relation(RelationKind.LEADS_TO, "destino", note="nota"))

    assert OntologyValidator.errors((origin, target)) == []


def test_validator_rejects_repeated_key() -> None:
    assert OntologyValidator.errors((concept("igual"), concept("igual"))) == [
        "igual: key repetida",
    ]


def test_validator_rejects_relation_to_unknown_target() -> None:
    origin = concept("origem", Relation(RelationKind.LEADS_TO, "fantasma", note="nota"))

    assert OntologyValidator.errors((origin,)) == ["origem: destino inexistente fantasma"]


@pytest.mark.parametrize("origin", [Origin.INFERRED, Origin.ABSENT])
def test_validator_requires_caveat_when_origin_needs_it(origin: Origin) -> None:
    ontology = replace(concept("sem_aviso"), origin=origin)

    assert OntologyValidator.errors((ontology,)) == [f"sem_aviso: {origin.name} exige caveat"]


@pytest.mark.parametrize("origin", [Origin.INFERRED, Origin.ABSENT])
def test_validator_rejects_blank_caveat(origin: Origin) -> None:
    ontology = replace(concept("aviso_vazio"), origin=origin, caveat=" ")

    assert OntologyValidator.errors((ontology,)) == [f"aviso_vazio: {origin.name} exige caveat"]


@pytest.mark.parametrize("origin", [Origin.CONFIRMED, Origin.POLICY])
def test_validator_does_not_require_caveat_for_other_origins(origin: Origin) -> None:
    assert OntologyValidator.errors((replace(concept("livre"), origin=origin),)) == []


@pytest.mark.parametrize(
    "relation",
    [
        Relation(RelationKind.NOT_IMPLIES, "destino", note="nota"),
        Relation(RelationKind.NOT_IMPLIES, "destino", note="nota", evidence=" "),
        Relation(RelationKind.NOT_IMPLIES, "destino", note=" ", evidence="medido"),
    ],
)
def test_validator_requires_evidence_and_note_in_not_implies(relation: Relation) -> None:
    errors = OntologyValidator.errors((concept("origem", relation), concept("destino")))

    assert errors == ["origem: NOT_IMPLIES destino exige evidence e note"]


def test_not_implies_with_evidence_and_note_is_valid() -> None:
    relation = Relation(RelationKind.NOT_IMPLIES, "destino", note="nota", evidence="medido")

    assert OntologyValidator.errors((concept("origem", relation), concept("destino"))) == []
