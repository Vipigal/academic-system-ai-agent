from typing import Annotated

from pydantic import Field

from api.application.agent.tool_arguments import FIRST_PAGE_ARGUMENT, PageArgument
from api.application.protocol.dto import catalog, detail, proposal, request
from api.application.protocol.service import ProtocolService
from api.application.shared.tool_parameters import (
    EnrollmentArgument,
    PeriodArgument,
    SubjectArgument,
    Teaching,
)
from api.application.shared.tool_result import ToolResult
from api.domain.protocol.action import ProtocolAction
from api.domain.protocol.catalog import ServiceArea
from api.domain.protocol.status import ProtocolStage


class ProtocolTools:
    def __init__(self, service: ProtocolService) -> None:
        self._service = service

    async def list_services(
        self, area: ServiceArea | None = None
    ) -> ToolResult[list[catalog.ServiceOfferDto]]:
        """Lista os serviços com taxa, prazo e se o agente pode abrir para este aluno.

        Use para o que o aluno pode pedir. Só ofereça abrir os com available true.
        """
        return await self._service.list_services(area)

    async def list_protocols(
        self,
        status: ProtocolStage | None = None,
        service: Annotated[str | None, Teaching("o código do serviço, em texto", "DOC-001")] = None,
        period: PeriodArgument | None = None,
        page: PageArgument = FIRST_PAGE_ARGUMENT,
    ) -> ToolResult[list[request.ProtocolDto]]:
        """Lista os protocolos do aluno com situação de prazo, taxa e documentos.

        Use para pedidos em andamento, certificado emitido ou pedido aberto por responsável.
        """
        return await self._service.list_protocols(status, service, period, page)

    async def get_protocol(
        self, number: Annotated[str, Teaching("o número do protocolo, em texto", "20260024630")]
    ) -> ToolResult[detail.ProtocolDetailDto]:
        """Mostra um protocolo com andamento, prazo, mensagens públicas, documentos e taxa.

        Use quando o aluno informar o número do pedido.
        """
        return await self._service.get_protocol(number)

    async def propose_protocol(
        self,
        action: Annotated[
            ProtocolAction,
            Field(
                description="O que o pedido faz, com o efeito no nome. Trancar, cancelar e "
                "transferir valem para o curso inteiro, nunca para uma disciplina. O efeito de "
                "cada ação está na skill protocols."
            ),
        ],
        enrollment: Annotated[
            EnrollmentArgument,
            Field(description="A matrícula do pedido, como vem em list_enrollments."),
        ],
        subject: Annotated[
            SubjectArgument | None,
            Field(
                description="A disciplina que o aluno citou no pedido, mesmo de passagem. É null "
                "só se ele não citou nenhuma."
            ),
        ] = None,
    ) -> ToolResult[proposal.Proposal]:
        """Prepara um pedido gratuito para o aluno confirmar, sem abrir nada.

        Confira antes se o aluno fala do curso inteiro ou de uma disciplina. Recusa duplicado.
        """
        return await self._service.propose_protocol(action, enrollment, subject)
