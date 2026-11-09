from api.domain.protocol.action import ProtocolAction
from api.domain.protocol.action_catalog import ServiceActions

DECLARATION = ServiceActions.of_action(ProtocolAction.DECLARACAO_DE_MATRICULA)
INFORMATION = ServiceActions.of_action(ProtocolAction.INFORMACOES_GERAIS)
LOCK = ServiceActions.of_action(ProtocolAction.TRANCAR_CURSO_INTEIRO)
