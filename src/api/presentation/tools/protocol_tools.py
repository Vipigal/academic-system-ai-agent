from api.application.dto.protocol_detail_dto import ProtocolDetailDto
from api.application.dto.protocol_dto import ProtocolDto
from api.application.dto.protocol_proposal_dto import Proposal
from api.application.dto.protocol_service_dto import ServiceDto
from api.application.dto.tool_result import ToolResult
from api.application.page import FIRST_PAGE, PageRequest
from api.application.protocol_service import ProtocolService
from api.domain.ontology import limits, protocols
from api.domain.protocol_catalog import ServiceArea
from api.domain.protocol_status import ProtocolStage
from api.presentation.tools.registry import ToolRegistry


class ProtocolTools:
    def __init__(self, service: ProtocolService) -> None:
        self._service = service

    @ToolRegistry.declares(
        protocols.SERVICO, protocols.TAXA_DE_SERVICO, protocols.PRAZO_DE_ATENDIMENTO
    )
    async def list_services(self, area: ServiceArea | None = None) -> ToolResult[list[ServiceDto]]:
        """Lista os serviços da secretaria com taxa, prazo e se o agente pode abrir.

        Use para saber o que o aluno pode pedir, quanto custa e quanto demora.
        """
        return await self._service.list_services(area)

    @ToolRegistry.declares(
        protocols.PROTOCOLO,
        protocols.DOCUMENTO_EMITIDO,
        protocols.PRAZO_DE_ATENDIMENTO,
        protocols.PEDIDO_DE_TERCEIRO,
    )
    async def list_protocols(
        self,
        status: ProtocolStage | None = None,
        service: str | None = None,
        period: str | None = None,
        page: PageRequest = FIRST_PAGE,
    ) -> ToolResult[list[ProtocolDto]]:
        """Lista os protocolos do aluno com situação de prazo, taxa e documentos.

        Use para pedidos em andamento, certificado emitido ou pedido aberto por responsável.
        """
        return await self._service.list_protocols(status, service, period, page)

    @ToolRegistry.declares(
        protocols.PROTOCOLO,
        protocols.DOCUMENTO_EMITIDO,
        protocols.TAXA_DE_SERVICO,
        limits.DADOS_INTERNOS,
    )
    async def get_protocol(self, number: str) -> ToolResult[ProtocolDetailDto]:
        """Mostra um protocolo com andamento, prazo, mensagens públicas, documentos e taxa.

        Use quando o aluno informar o número do pedido.
        """
        return await self._service.get_protocol(number)

    @ToolRegistry.declares(
        protocols.SERVICO, protocols.TAXA_DE_SERVICO, protocols.PRAZO_DE_ATENDIMENTO
    )
    async def propose_protocol(
        self, service: str, message: str, enrollment: str | None = None
    ) -> ToolResult[Proposal]:
        """Prepara um pedido gratuito para o aluno confirmar, sem abrir nada.

        Use para declaração, boleto, trancamento ou revisão. Recusa serviço com taxa ou duplicado.
        """
        return await self._service.propose_protocol(service, enrollment, message)
