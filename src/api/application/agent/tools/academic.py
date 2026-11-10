from typing import Annotated

from api.application.academic.dto import catalog, record
from api.application.academic.dto.curriculum import (
    NO_FILTER,
    CurriculumFilter,
    CurriculumSubjectDto,
)
from api.application.academic.dto.enrollment import EnrollmentDto
from api.application.academic.service import AcademicService
from api.application.agent.tool_arguments import FIRST_PAGE_ARGUMENT, PageArgument
from api.application.agent.tools.registry import ToolRegistry
from api.application.agent.tools.ui import ToolUi
from api.application.shared.tool_parameters import (
    EnrollmentArgument,
    FlagArgument,
    SubjectArgument,
    Teaching,
    TermArgument,
)
from api.application.shared.tool_result import ToolResult
from api.domain.ontology import academic_enrollment, academic_performance, limits, overview
from api.domain.shared.brand import Modality

PROGRESS_UI = "Painel do progresso no curso exibido ao aluno."


class AcademicTools:
    def __init__(self, service: AcademicService) -> None:
        self._service = service

    @ToolRegistry.declares(
        academic_enrollment.DATA_DE_REFERENCIA,
        academic_enrollment.CALENDARIO_2027,
        overview.PERIODO_COBERTO,
    )
    async def get_academic_calendar(
        self, term: TermArgument | None = None
    ) -> ToolResult[catalog.AcademicCalendarDto]:
        """Mostra as datas de um semestre e o último cadastrado.

        Use para saber o semestre atual, quando começam as AVs ou quando o semestre termina.
        """
        return await self._service.get_academic_calendar(term)

    @ToolRegistry.declares(academic_enrollment.OFERTA)
    async def list_course_offers(
        self,
        course: Annotated[str | None, Teaching("o nome do curso, em texto", "Enfermagem")] = None,
        modality: Modality | None = None,
        unit: Annotated[
            str | None, Teaching("o nome da unidade, em texto", "Campus Paulista")
        ] = None,
        page: PageArgument = FIRST_PAGE_ARGUMENT,
    ) -> ToolResult[list[catalog.CourseOfferDto]]:
        """Lista os cursos oferecidos na instituição do aluno, por unidade e turno.

        Use para saber se existe um curso, modalidade ou turno.
        """
        return await self._service.list_course_offers(course, modality, unit, page)

    @ToolRegistry.declares(
        academic_enrollment.MATRICULA,
        academic_enrollment.REMATRICULA,
        academic_enrollment.TRANCAMENTO,
        academic_performance.CR,
        academic_performance.CONCLUSAO,
    )
    async def list_enrollments(self) -> ToolResult[list[EnrollmentDto]]:
        """Lista as matrículas do aluno com situação e histórico.

        Use para vínculo, rematrícula, trancamento, CR ou conclusão do curso.
        """
        return await self._service.list_enrollments()

    @ToolRegistry.declares(
        academic_enrollment.MATRIZ,
        academic_enrollment.PRE_REQUISITO,
        academic_enrollment.TCC_E_ESTAGIO,
        academic_enrollment.PROJETO_INTEGRADOR,
        academic_performance.CONCLUSAO,
    )
    async def get_curriculum(
        self,
        enrollment: EnrollmentArgument | None = None,
        filters: Annotated[
            CurriculumFilter,
            Teaching(
                "um objeto com semester, subject e pending_only, todos opcionais",
                '{"semester": 3, "pending_only": true}',
            ),
        ] = NO_FILTER,
        *,
        page: PageArgument = FIRST_PAGE_ARGUMENT,
        show_ui: FlagArgument = False,
    ) -> ToolResult[list[CurriculumSubjectDto]]:
        """Mostra a matriz do aluno com a situação em cada disciplina.

        Use para disciplinas por semestre, pré-requisitos, TCC, estágio ou o que falta.
        Pode mostrar UI ao aluno com show_ui.
        """
        curriculum = await self._service.get_curriculum(
            enrollment,
            filters.semester,
            filters.subject,
            pending_only=filters.pending_only,
            page=page,
        )
        return ToolUi.shown(curriculum, PROGRESS_UI) if show_ui else curriculum

    @ToolRegistry.declares(
        academic_performance.RESULTADO,
        academic_performance.AV,
        academic_performance.MEDIA,
        academic_performance.CRITERIO_DE_APROVACAO,
        academic_performance.FREQUENCIA,
        academic_performance.REGISTRO_OFICIAL,
    )
    async def list_subject_records(
        self,
        enrollment: EnrollmentArgument | None = None,
        term: TermArgument | None = None,
        subject: SubjectArgument | None = None,
        page: PageArgument = FIRST_PAGE_ARGUMENT,
    ) -> ToolResult[list[record.SubjectRecordDto]]:
        """Lista as disciplinas cursadas com notas, frequência e resultado.

        Use para ver o semestre atual, uma nota, uma reprovação ou a nota necessária na AV2.
        """
        return await self._service.list_subject_records(enrollment, term, subject, page)

    @ToolRegistry.declares(limits.DADOS_INTERNOS)
    async def list_subject_professors(
        self, subject: SubjectArgument, term: TermArgument | None = None
    ) -> ToolResult[list[catalog.SubjectProfessorDto]]:
        """Lista quem leciona uma disciplina em um semestre, na instituição do aluno.

        Use para saber quem é o professor e como contatá-lo.
        """
        return await self._service.list_subject_professors(subject, term)
