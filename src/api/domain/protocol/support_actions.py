from api.domain.protocol.action import ONLY_ACTIVE, ProtocolAction, ServiceAction

SEGUNDA_VIA_DE_BOLETO = ServiceAction(
    code="FIN-030",
    action=ProtocolAction.SEGUNDA_VIA_DE_BOLETO,
    title="Segunda via de boleto",
    effect="Pede a reemissão de um boleto.",
    confirmation_question="Confirma o pedido de segunda via de boleto do curso {course}?",
    request_text="Solicito a segunda via de um boleto.",
)

RENEGOCIACAO = ServiceAction(
    code="FIN-031",
    action=ProtocolAction.RENEGOCIAR_DIVIDA,
    title="Renegociação de dívida",
    effect="Pede a renegociação da dívida. O pedido atendido leva a um acordo.",
    confirmation_question="Tem certeza de que deseja pedir a renegociação da dívida do curso "
    "{course}?",
    confirmation_word="RENEGOCIAR",
    request_text="Solicito a renegociação da minha dívida.",
)

DESCONTO_OU_BOLSA = ServiceAction(
    code="FIN-032",
    action=ProtocolAction.PEDIR_DESCONTO_OU_BOLSA,
    title="Pedido de desconto ou bolsa",
    effect="Pede um desconto ou uma bolsa à secretaria.",
    not_for="Não garante o desconto nem a bolsa: os critérios não estão nos dados.",
    accepted_statuses=ONLY_ACTIVE,
    confirmation_question="Confirma o pedido de desconto ou bolsa no curso {course}?",
    request_text="Solicito um desconto ou uma bolsa.",
)

INFORMACOES_GERAIS = ServiceAction(
    code="GEN-090",
    action=ProtocolAction.INFORMACOES_GERAIS,
    title="Informações gerais",
    effect="Envia uma pergunta à secretaria.",
    not_for="Não garante a solução do caso.",
    accepts_subject=True,
    confirmation_question="Confirma o pedido de informações no curso {course}?",
    request_text="Solicito informações à secretaria.",
    requires_student_message=True,
)

RECLAMACAO = ServiceAction(
    code="OUV-099",
    action=ProtocolAction.RECLAMACAO_NA_OUVIDORIA,
    title="Reclamação na ouvidoria",
    effect="Registra uma reclamação na ouvidoria.",
    accepts_subject=True,
    confirmation_question="Confirma o registro da reclamação no curso {course}?",
    request_text="Registro uma reclamação na ouvidoria.",
    requires_student_message=True,
)

ACESSO_AO_AVA = ServiceAction(
    code="TEC-060",
    action=ProtocolAction.PROBLEMA_DE_ACESSO_AO_AVA,
    title="Problema de acesso ao AVA",
    effect="Pede ajuda com o acesso ao ambiente virtual de aprendizagem.",
    accepted_statuses=ONLY_ACTIVE,
    accepts_subject=True,
    confirmation_question="Confirma o pedido de ajuda com o acesso ao AVA no curso {course}?",
    request_text="Solicito ajuda com o acesso ao ambiente virtual.",
    requires_student_message=True,
)

SUPPORT_ACTIONS = (
    SEGUNDA_VIA_DE_BOLETO,
    RENEGOCIACAO,
    DESCONTO_OU_BOLSA,
    INFORMACOES_GERAIS,
    RECLAMACAO,
    ACESSO_AO_AVA,
)
