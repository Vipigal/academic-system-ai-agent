from typing import NamedTuple

import pytest

from api.domain.academic.enrollment import EnrollmentStatus
from api.domain.protocol.action import ProtocolAction, ServiceAction
from api.domain.protocol.action_catalog import SERVICE_ACTIONS, ServiceActions

DEMAND_TYPE_CODES = {
    "ACA-010",
    "ACA-011",
    "ACA-012",
    "ACA-013",
    "ACA-014",
    "ACA-020",
    "ACA-021",
    "DOC-001",
    "DOC-002",
    "DOC-003",
    "DOC-040",
    "DOC-041",
    "FIN-030",
    "FIN-031",
    "FIN-032",
    "GEN-090",
    "OUV-099",
    "TEC-060",
}
WITH_FEE = {"ACA-021", "DOC-002", "DOC-003", "DOC-041"}
FREE_TEXT = {"ACA-020", "GEN-090", "OUV-099", "TEC-060"}
ACTIVE = frozenset({EnrollmentStatus.ACTIVE})
ACTIVE_OR_LOCKED = frozenset({EnrollmentStatus.ACTIVE, EnrollmentStatus.LOCKED})
ANY = frozenset(EnrollmentStatus)


class ActionRow(NamedTuple):
    code: str
    action: str
    statuses: frozenset[EnrollmentStatus]
    word: str | None


ACTION_TABLE: list[ActionRow] = [
    ActionRow("ACA-010", "trancar_curso_inteiro", ACTIVE, "TRANCAR"),
    ActionRow("ACA-011", "reativar_matricula", frozenset({EnrollmentStatus.LOCKED}), None),
    ActionRow("ACA-012", "cancelar_curso_inteiro", ACTIVE, "CANCELAR"),
    ActionRow("ACA-013", "transferir_de_curso", ACTIVE, "TRANSFERIR"),
    ActionRow("ACA-014", "migrar_matriz_curricular", ACTIVE_OR_LOCKED, "MIGRAR"),
    ActionRow("ACA-020", "revisar_nota", ACTIVE_OR_LOCKED, None),
    ActionRow("DOC-001", "declaracao_de_matricula", ACTIVE, None),
    ActionRow("DOC-040", "emitir_diploma", frozenset({EnrollmentStatus.GRADUATED}), None),
    ActionRow("FIN-030", "segunda_via_de_boleto", ANY, None),
    ActionRow("FIN-031", "renegociar_divida", ANY, "RENEGOCIAR"),
    ActionRow("FIN-032", "pedir_desconto_ou_bolsa", ACTIVE, None),
    ActionRow("GEN-090", "informacoes_gerais", ANY, None),
    ActionRow("OUV-099", "reclamacao_na_ouvidoria", ANY, None),
    ActionRow("TEC-060", "problema_de_acesso_ao_ava", ACTIVE, None),
]


def test_the_catalog_covers_exactly_the_18_demand_types_once() -> None:
    codes = [item.code for item in SERVICE_ACTIONS]

    assert len(codes) == len(set(codes))
    assert set(codes) == DEMAND_TYPE_CODES


@pytest.mark.parametrize("entry", SERVICE_ACTIONS, ids=lambda entry: entry.code)
def test_every_entry_has_title_effect_and_fixed_request_text(entry: ServiceAction) -> None:
    assert entry == ServiceActions.find(entry.code)
    assert entry.title.strip()
    assert entry.effect.strip()
    assert entry.request_text.strip()
    assert isinstance(entry.requires_student_message, bool)


@pytest.mark.parametrize("row", ACTION_TABLE, ids=lambda row: row.code)
def test_each_proposable_service_follows_the_action_table(row: ActionRow) -> None:
    entry = ServiceActions.proposable(row.code)

    assert entry is not None
    assert entry.action is ProtocolAction(row.action)
    assert (entry.accepted_statuses, entry.confirmation_word) == (row.statuses, row.word)
    assert ServiceActions.of_action(ProtocolAction(row.action)) is entry


def test_every_action_belongs_to_exactly_one_service() -> None:
    actions = [item.action for item in SERVICE_ACTIONS if item.action is not None]

    assert sorted(actions, key=str) == sorted(ProtocolAction, key=str)


@pytest.mark.parametrize("code", sorted(WITH_FEE))
def test_services_with_fee_have_title_and_effect_but_no_action(code: str) -> None:
    entry = ServiceActions.find(code)

    assert entry is not None
    assert entry.action is None
    assert ServiceActions.proposable(code) is None


def test_only_the_free_text_services_take_the_student_message() -> None:
    assert {item.code for item in SERVICE_ACTIONS if item.requires_student_message} == FREE_TEXT


def test_only_the_free_text_services_accept_a_subject() -> None:
    assert {item.code for item in SERVICE_ACTIONS if item.accepts_subject} == FREE_TEXT


@pytest.mark.parametrize("code", ["XYZ-999", "aca-010", ""])
def test_an_unknown_code_fails_closed(code: str) -> None:
    assert ServiceActions.find(code) is None
    assert ServiceActions.proposable(code) is None


def test_the_confirmation_question_names_the_course() -> None:
    entry = ServiceActions.of_action(ProtocolAction.TRANCAR_CURSO_INTEIRO)

    assert entry.question_for("Ciências Contábeis") == (
        "Tem certeza de que deseja trancar o curso Ciências Contábeis?"
    )
    assert entry.not_for == "Não tranca uma disciplina."


def test_every_action_has_a_confirmation_question() -> None:
    assert all(item.question_for("Direito") for item in SERVICE_ACTIONS if item.action is not None)


def test_a_service_without_action_has_no_confirmation_question() -> None:
    entry = ServiceActions.find("DOC-041")

    assert entry is not None
    assert entry.question_for("Direito") is None


def test_the_lock_accepts_only_an_active_enrollment() -> None:
    entry = ServiceActions.of_action(ProtocolAction.TRANCAR_CURSO_INTEIRO)

    assert entry.accepts(EnrollmentStatus.ACTIVE)
    assert not entry.accepts(EnrollmentStatus.LOCKED)


def test_the_renegotiation_leads_to_an_agreement() -> None:
    assert "leva a um acordo" in ServiceActions.of_action(ProtocolAction.RENEGOCIAR_DIVIDA).effect


def test_no_effect_or_limit_talks_about_charges() -> None:
    texts = [text for item in SERVICE_ACTIONS for text in (item.effect, item.not_for or "")]

    assert not [text for text in texts if "cobran" in text.casefold()]


def test_titles_are_indexed_by_code() -> None:
    titles = ServiceActions.titles()

    assert set(titles) == DEMAND_TYPE_CODES
    assert titles["ACA-020"] == "Revisão de nota"
