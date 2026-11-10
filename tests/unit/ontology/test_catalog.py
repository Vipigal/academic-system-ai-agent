from collections import Counter

from api.domain.ontology.academic_enrollment import (
    DATA_DE_REFERENCIA,
    MATRICULA,
    MATRICULA_EM_DISCIPLINA,
    TRANCAMENTO,
)
from api.domain.ontology.catalog import ONTOLOGIES
from api.domain.protocol.action import ProtocolAction
from api.domain.protocol.action_catalog import SERVICE_ACTIONS


def test_catalog_keys_are_unique() -> None:
    repeated = [
        key for key, amount in Counter(item.key for item in ONTOLOGIES).items() if amount > 1
    ]

    assert repeated == []


def test_every_relation_targets_an_existing_concept() -> None:
    keys = {item.key for item in ONTOLOGIES}
    targets = {relation.target for item in ONTOLOGIES for relation in item.relations}

    assert targets <= keys


def test_lock_synonyms_name_the_whole_course() -> None:
    assert "trancar" not in TRANCAMENTO.synonyms
    assert {"trancar o curso", "trancar a matrícula do curso", "parar o curso"} <= set(
        TRANCAMENTO.synonyms
    )
    assert "curso inteiro" in TRANCAMENTO.definition


def test_enrollment_says_the_student_also_calls_a_subject_an_enrollment() -> None:
    assert "inscrição numa disciplina" in MATRICULA.definition


def test_subject_enrollment_only_explains_and_is_never_offered() -> None:
    offered = {action.value for action in ProtocolAction} | {item.title for item in SERVICE_ACTIONS}

    assert MATRICULA_EM_DISCIPLINA.name not in offered
    assert any("Oferecer" in item for item in MATRICULA_EM_DISCIPLINA.never_say)
    assert "Não é um serviço" in MATRICULA_EM_DISCIPLINA.definition


def test_reference_date_is_today_with_no_fixed_date() -> None:
    assert "data de hoje" in DATA_DE_REFERENCIA.definition
    assert "2026" not in DATA_DE_REFERENCIA.definition
