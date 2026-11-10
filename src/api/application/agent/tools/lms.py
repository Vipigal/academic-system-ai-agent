from typing import Annotated

from api.application.agent.tool_arguments import FIRST_PAGE_ARGUMENT, PageArgument
from api.application.agent.tools.ui import ToolUi
from api.application.lms.dto.account import LmsAccountDto
from api.application.lms.dto.exam import OnlineExamDto
from api.application.lms.dto.material import MaterialViewDto
from api.application.lms.service import LmsService
from api.application.shared.tool_parameters import (
    FlagArgument,
    SubjectArgument,
    Teaching,
    TermArgument,
)
from api.application.shared.tool_result import ToolResult

EXAMS_UI = "Calendário das provas online exibido ao aluno."


class LmsTools:
    def __init__(self, service: LmsService) -> None:
        self._service = service

    async def list_online_exams(
        self,
        subject: SubjectArgument | None = None,
        term: TermArgument | None = None,
        page: PageArgument = FIRST_PAGE_ARGUMENT,
        *,
        show_ui: FlagArgument = False,
    ) -> ToolResult[list[OnlineExamDto]]:
        """Lista as provas online com janela, tentativas e nota do AVA e do histórico.

        Use para prazo, tentativas restantes, entrega registrada ou nota de AV e simulado.
        Pode mostrar UI ao aluno com show_ui.
        """
        exams = await self._service.list_online_exams(subject, term, page)
        return ToolUi.shown(exams, EXAMS_UI) if show_ui else exams

    async def get_lms_account(self) -> ToolResult[list[LmsAccountDto]]:
        """Mostra, por matrícula, se há conta no AVA, se está suspensa e o último acesso.

        Use quando o aluno não consegue entrar no AVA ou pergunta do último acesso.
        """
        return await self._service.get_lms_account()

    async def list_material_views(
        self,
        subject: SubjectArgument,
        query: Annotated[
            str | None, Teaching("um trecho do título do material", "Semana 2")
        ] = None,
        page: PageArgument = FIRST_PAGE_ARGUMENT,
    ) -> ToolResult[list[MaterialViewDto]]:
        """Lista os materiais de uma disciplina no AVA com os acessos do aluno, sem o conteúdo.

        Use para saber se o aluno já abriu um material, como a aula de uma semana.
        """
        return await self._service.list_material_views(subject, query, page)
