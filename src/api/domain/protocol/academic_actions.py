from api.domain.academic.enrollment import EnrollmentStatus
from api.domain.protocol.action import ProtocolAction, ServiceAction

ONLY_ACTIVE = frozenset({EnrollmentStatus.ACTIVE})

TRANCAMENTO = ServiceAction(
    code="ACA-010",
    action=ProtocolAction.TRANCAR_CURSO_INTEIRO,
    title="Trancamento do curso",
    effect="Tranca a matrícula no curso inteiro: a situação passa de ativa para trancada.",
    not_for="Não tranca uma disciplina.",
    accepted_statuses=ONLY_ACTIVE,
    confirmation_question="Tem certeza de que deseja trancar o curso {course}?",
    confirmation_word="TRANCAR",
    request_text="Solicito o trancamento da minha matrícula no curso.",
)

REATIVACAO = ServiceAction(
    code="ACA-011",
    action=ProtocolAction.REATIVAR_MATRICULA,
    title="Reativação de matrícula",
    effect="Reativa a matrícula trancada: a situação passa de trancada para ativa.",
    not_for="Não reativa matrícula cancelada, transferida ou concluída.",
    accepted_statuses=frozenset({EnrollmentStatus.LOCKED}),
    confirmation_question="Confirma o pedido de reativação da matrícula no curso {course}?",
    request_text="Solicito a reativação da minha matrícula trancada.",
)

CANCELAMENTO = ServiceAction(
    code="ACA-012",
    action=ProtocolAction.CANCELAR_CURSO_INTEIRO,
    title="Cancelamento do curso",
    effect="Cancela a matrícula no curso inteiro: a situação passa de ativa para cancelada.",
    not_for="Não cancela uma disciplina.",
    accepted_statuses=ONLY_ACTIVE,
    confirmation_question="Tem certeza de que deseja cancelar o curso {course}?",
    confirmation_word="CANCELAR",
    request_text="Solicito o cancelamento da minha matrícula no curso.",
)

TRANSFERENCIA = ServiceAction(
    code="ACA-013",
    action=ProtocolAction.TRANSFERIR_DE_CURSO,
    title="Transferência interna",
    effect="Encerra a matrícula atual como transferida e abre outra, em outro curso ou no mesmo "
    "curso em outra modalidade.",
    not_for="Não troca uma disciplina.",
    accepted_statuses=ONLY_ACTIVE,
    confirmation_question="Tem certeza de que deseja transferir a matrícula do curso {course}?",
    confirmation_word="TRANSFERIR",
    request_text="Solicito a transferência interna da minha matrícula.",
)

MIGRACAO_DE_MATRIZ = ServiceAction(
    code="ACA-014",
    action=ProtocolAction.MIGRAR_MATRIZ_CURRICULAR,
    title="Migração de matriz curricular",
    effect="Muda a matriz curricular da matrícula; a situação da matrícula não muda.",
    not_for="Não muda de curso.",
    accepted_statuses=frozenset({EnrollmentStatus.ACTIVE, EnrollmentStatus.LOCKED}),
    confirmation_question="Tem certeza de que deseja migrar a matriz curricular do curso {course}?",
    confirmation_word="MIGRAR",
    request_text="Solicito a migração da minha matrícula para outra matriz curricular.",
)

REVISAO_DE_NOTA = ServiceAction(
    code="ACA-020",
    action=ProtocolAction.REVISAR_NOTA,
    title="Revisão de nota",
    effect="Pede à secretaria a revisão de uma nota.",
    not_for="Não garante a mudança da nota.",
    accepts_subject=True,
    confirmation_question="Confirma o pedido de revisão de nota no curso {course}?",
    request_text="Solicito a revisão de uma nota.",
    requires_student_message=True,
)

SEGUNDA_CHAMADA = ServiceAction(
    code="ACA-021",
    action=None,
    title="Prova de segunda chamada",
    effect="Pede uma prova de segunda chamada. Tem taxa, e o pedido é feito com a secretaria.",
    request_text="Solicito uma prova de segunda chamada.",
)

ACADEMIC_ACTIONS = (
    TRANCAMENTO,
    REATIVACAO,
    CANCELAMENTO,
    TRANSFERENCIA,
    MIGRACAO_DE_MATRIZ,
    REVISAO_DE_NOTA,
    SEGUNDA_CHAMADA,
)
