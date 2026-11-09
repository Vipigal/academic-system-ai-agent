import pytest

from api.application.agent.action_table import ActionTable
from api.application.agent.skill_library import SkillLibrary
from api.domain.ontology.academic_enrollment import MATRICULA_EM_DISCIPLINA
from api.domain.ontology.model import Area
from api.domain.protocol.action import ProtocolAction, ServiceAction
from api.domain.protocol.action_catalog import SERVICE_ACTIONS

TABLE = ActionTable.render()
LIBRARY = SkillLibrary.load()
PROPOSABLE = [item for item in SERVICE_ACTIONS if item.action is not None]
WITH_FEE = [item for item in SERVICE_ACTIONS if item.action is None]
EXPECTED_ROWS = {
    "trancar_curso_inteiro": "| `trancar_curso_inteiro` | ACA-010, Trancamento do curso | Tranca a "
    "matrícula no curso inteiro: a situação passa de ativa para trancada. Não tranca uma "
    "disciplina. | `active` | recusa | texto fixo da ação; o aluno digita a palavra de "
    "confirmação |",
    "revisar_nota": "| `revisar_nota` | ACA-020, Revisão de nota | Pede à secretaria a revisão de "
    "uma nota. Não garante a mudança da nota. | qualquer | aceita | o aluno escreve a mensagem |",
    "migrar_matriz_curricular": "| `migrar_matriz_curricular` | ACA-014, Migração de matriz "
    "curricular | Muda a matriz curricular da matrícula; a situação da matrícula não muda. "
    "Não muda de curso. | `active`, `locked` | recusa | texto fixo da ação; o aluno digita a "
    "palavra de confirmação |",
    "declaracao_de_matricula": "| `declaracao_de_matricula` | DOC-001, Declaração de matrícula | "
    "Emite uma declaração de matrícula, com código de validação. | qualquer | recusa | texto fixo "
    "da ação |",
}


def row_of(action: ProtocolAction) -> str:
    rows = [line for line in TABLE.splitlines() if line.startswith(f"| `{action.value}` |")]
    assert len(rows) == 1
    return rows[0]


def test_the_table_has_one_row_per_action() -> None:
    lines = TABLE.splitlines()

    assert [row_of(action) for action in ProtocolAction] == lines[-len(ProtocolAction) :]
    assert lines[2] == "| `action` | Serviço | O que faz | Matrícula aceita | `subject` | No card |"


@pytest.mark.parametrize("item", PROPOSABLE, ids=lambda item: item.code)
def test_each_row_carries_the_code_title_and_effect_of_the_catalog(item: ServiceAction) -> None:
    assert item.action is not None
    row = row_of(item.action)

    assert f"{item.code}, {item.title}" in row
    assert item.effect in row
    assert item.not_for is None or item.not_for in row


@pytest.mark.parametrize("item", WITH_FEE, ids=lambda item: item.code)
def test_services_without_action_stay_out_of_the_table(item: ServiceAction) -> None:
    assert item.code not in TABLE


@pytest.mark.parametrize(("action", "expected"), EXPECTED_ROWS.items())
def test_the_row_reads_as_the_snapshot(action: str, expected: str) -> None:
    assert row_of(ProtocolAction(action)) == expected


def test_the_table_never_offers_a_subject_lock() -> None:
    assert MATRICULA_EM_DISCIPLINA.key not in TABLE
    assert MATRICULA_EM_DISCIPLINA.name not in TABLE
    assert "trancar_disciplina" not in TABLE


def test_the_table_never_shows_the_confirmation_word() -> None:
    words = [item.confirmation_word for item in SERVICE_ACTIONS if item.confirmation_word]

    assert [word for word in words if word in TABLE] == []


def test_only_the_protocols_skill_carries_the_table() -> None:
    carrying = [area for area in Area if TABLE in LIBRARY.instructions(area)]

    assert carrying == [Area.PROTOCOLS]


def test_the_table_comes_after_the_protocols_body_and_before_the_concepts() -> None:
    instructions = LIBRARY.instructions(Area.PROTOCOLS)

    assert instructions.index("# Protocolos") < instructions.index(TABLE)
    assert instructions.index(TABLE) < instructions.index("### Protocolo (`protocolo`)")
