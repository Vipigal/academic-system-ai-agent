from api.application.agent.tools.registry import ToolRegistry
from api.application.lms.dto.account import LmsAccountDto
from api.application.lms.dto.exam import OnlineExamDto
from api.application.lms.dto.material import MaterialViewDto
from api.application.lms.service import LmsService
from api.application.shared.page import FIRST_PAGE, PageRequest
from api.application.shared.tool_result import ToolResult
from api.domain.ontology import lms, overview


class LmsTools:
    def __init__(self, service: LmsService) -> None:
        self._service = service

    @ToolRegistry.declares(
        lms.PROVA_ONLINE,
        lms.TENTATIVA,
        lms.NOTA_DO_AVA,
        lms.GABARITO,
        overview.PERIODO_COBERTO,
    )
    async def list_online_exams(
        self,
        subject: str | None = None,
        term: str | None = None,
        page: PageRequest = FIRST_PAGE,
    ) -> ToolResult[list[OnlineExamDto]]:
        """Lista as provas online do aluno com janela, tentativas e nota do AVA e do histórico.

        Use para prazo, tentativas restantes, entrega registrada ou nota de AV e simulado.
        """
        return await self._service.list_online_exams(subject, term, page)

    @ToolRegistry.declares(lms.ULTIMO_ACESSO, lms.SUSPENSAO_DO_AVA)
    async def get_lms_account(self) -> ToolResult[list[LmsAccountDto]]:
        """Mostra, por matrícula, se há conta no AVA, se está suspensa e o último acesso.

        Use quando o aluno não consegue entrar no AVA ou pergunta do último acesso.
        """
        return await self._service.get_lms_account()

    @ToolRegistry.declares(lms.VISUALIZACAO_DE_MATERIAL)
    async def list_material_views(
        self, subject: str, query: str | None = None, page: PageRequest = FIRST_PAGE
    ) -> ToolResult[list[MaterialViewDto]]:
        """Lista os materiais de uma disciplina no AVA com os acessos do aluno, sem o conteúdo.

        Use para saber se o aluno já abriu um material, como a aula de uma semana.
        """
        return await self._service.list_material_views(subject, query, page)
