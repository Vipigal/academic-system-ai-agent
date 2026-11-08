from collections.abc import Sequence

from api.domain.academic.enrollment import EnrollmentStatus
from api.domain.protocol.action import ANY_STATUS, ProtocolAction, ServiceAction
from api.domain.protocol.action_catalog import SERVICE_ACTIONS

HEADING = "## Ações de `propose_protocol`"
COLUMNS = ("`action`", "Serviço", "O que faz", "Matrícula aceita", "`subject`", "No card")
ANY_ENROLLMENT = "qualquer"
SUBJECT_ACCEPTED = "aceita"
SUBJECT_REFUSED = "recusa"
STUDENT_WRITES = "o aluno escreve a mensagem"
FIXED_TEXT = "texto fixo da ação"
WORD_TYPED = "o aluno digita a palavra de confirmação"
LINE_SEPARATOR = "\n"
LIST_SEPARATOR = ", "
CARD_SEPARATOR = "; "
CELL_SEPARATOR = " | "


class ActionTable:
    @classmethod
    def render(cls, actions: Sequence[ServiceAction] = SERVICE_ACTIONS) -> str:
        proposable = ((item, item.action) for item in actions if item.action is not None)
        rows = [cls._row(item, action) for item, action in proposable]
        divider = cls._line(("---",) * len(COLUMNS))
        return LINE_SEPARATOR.join((HEADING, "", cls._line(COLUMNS), divider, *rows))

    @classmethod
    def _row(cls, item: ServiceAction, action: ProtocolAction) -> str:
        effect = " ".join(text for text in (item.effect, item.not_for) if text)
        subject = SUBJECT_ACCEPTED if item.accepts_subject else SUBJECT_REFUSED
        cells = (
            f"`{action.value}`",
            f"{item.code}, {item.title}",
            effect,
            cls._statuses(item.accepted_statuses),
            subject,
            cls._card(item),
        )
        return cls._line(cells)

    @staticmethod
    def _statuses(statuses: frozenset[EnrollmentStatus]) -> str:
        if statuses == ANY_STATUS:
            return ANY_ENROLLMENT
        accepted = (item for item in EnrollmentStatus if item in statuses)
        return LIST_SEPARATOR.join(f"`{item.value}`" for item in accepted)

    @staticmethod
    def _card(item: ServiceAction) -> str:
        message = STUDENT_WRITES if item.requires_student_message else FIXED_TEXT
        if item.confirmation_word is None:
            return message
        return CARD_SEPARATOR.join((message, WORD_TYPED))

    @staticmethod
    def _line(cells: Sequence[str]) -> str:
        joined = CELL_SEPARATOR.join(cells)
        return f"| {joined} |"
