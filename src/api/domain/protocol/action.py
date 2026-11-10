from dataclasses import dataclass
from enum import Enum

from api.domain.academic.enrollment import EnrollmentStatus

ANY_STATUS = frozenset(EnrollmentStatus)
ONLY_ACTIVE = frozenset({EnrollmentStatus.ACTIVE})
ACTIVE_OR_LOCKED = frozenset({EnrollmentStatus.ACTIVE, EnrollmentStatus.LOCKED})
ONLY_GRADUATED = frozenset({EnrollmentStatus.GRADUATED})


class ProtocolAction(Enum):
    TRANCAR_CURSO_INTEIRO = "trancar_curso_inteiro"
    REATIVAR_MATRICULA = "reativar_matricula"
    CANCELAR_CURSO_INTEIRO = "cancelar_curso_inteiro"
    TRANSFERIR_DE_CURSO = "transferir_de_curso"
    MIGRAR_MATRIZ_CURRICULAR = "migrar_matriz_curricular"
    REVISAR_NOTA = "revisar_nota"
    DECLARACAO_DE_MATRICULA = "declaracao_de_matricula"
    EMITIR_DIPLOMA = "emitir_diploma"
    SEGUNDA_VIA_DE_BOLETO = "segunda_via_de_boleto"
    RENEGOCIAR_DIVIDA = "renegociar_divida"
    PEDIR_DESCONTO_OU_BOLSA = "pedir_desconto_ou_bolsa"
    INFORMACOES_GERAIS = "informacoes_gerais"
    RECLAMACAO_NA_OUVIDORIA = "reclamacao_na_ouvidoria"
    PROBLEMA_DE_ACESSO_AO_AVA = "problema_de_acesso_ao_ava"


@dataclass(frozen=True, slots=True, kw_only=True)
class ServiceAction:
    code: str
    action: ProtocolAction | None
    title: str
    effect: str
    not_for: str | None = None
    accepted_statuses: frozenset[EnrollmentStatus] = ANY_STATUS
    accepts_subject: bool = False
    confirmation_question: str | None = None
    confirmation_word: str | None = None
    request_text: str
    requires_student_message: bool = False

    def accepts(self, status: EnrollmentStatus) -> bool:
        return status in self.accepted_statuses

    def question_for(self, course: str) -> str | None:
        if self.confirmation_question is None:
            return None
        return self.confirmation_question.format(course=course)
