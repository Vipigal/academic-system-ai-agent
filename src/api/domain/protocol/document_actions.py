from api.domain.protocol.action import ProtocolAction, ServiceAction

DECLARACAO_DE_MATRICULA = ServiceAction(
    code="DOC-001",
    action=ProtocolAction.DECLARACAO_DE_MATRICULA,
    title="Declaração de matrícula",
    effect="Emite uma declaração de matrícula, com código de validação.",
    confirmation_question="Confirma o pedido de declaração de matrícula no curso {course}?",
    request_text="Solicito uma declaração de matrícula.",
)

HISTORICO_IMPRESSO = ServiceAction(
    code="DOC-002",
    action=None,
    title="Histórico escolar impresso",
    effect="Emite o histórico escolar impresso. Tem taxa, e o pedido é feito com a secretaria.",
    request_text="Solicito o histórico escolar impresso.",
)

PACOTE_DE_EMENTAS = ServiceAction(
    code="DOC-003",
    action=None,
    title="Pacote de ementas",
    effect="Emite as ementas das disciplinas. Tem taxa, e o pedido é feito com a secretaria.",
    request_text="Solicito o pacote de ementas.",
)

EMISSAO_DE_DIPLOMA = ServiceAction(
    code="DOC-040",
    action=ProtocolAction.EMITIR_DIPLOMA,
    title="Emissão de diploma",
    effect="Emite o diploma e o certificado de conclusão.",
    confirmation_question="Confirma o pedido de emissão do diploma do curso {course}?",
    request_text="Solicito a emissão do meu diploma.",
)

SEGUNDA_VIA_DE_DIPLOMA = ServiceAction(
    code="DOC-041",
    action=None,
    title="Segunda via de diploma",
    effect="Emite uma segunda via do diploma. Tem taxa, e o pedido é feito com a secretaria.",
    request_text="Solicito a segunda via do meu diploma.",
)

DOCUMENT_ACTIONS = (
    DECLARACAO_DE_MATRICULA,
    HISTORICO_IMPRESSO,
    PACOTE_DE_EMENTAS,
    EMISSAO_DE_DIPLOMA,
    SEGUNDA_VIA_DE_DIPLOMA,
)
