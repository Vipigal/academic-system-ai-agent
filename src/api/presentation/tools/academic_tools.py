from api.application.academic_service import AcademicService
from api.application.dto.academic_catalog_dto import (
    AcademicCalendarDto,
    CourseOfferDto,
    SubjectProfessorDto,
)
from api.application.dto.academic_curriculum_dto import CurriculumSubjectDto
from api.application.dto.academic_enrollment_dto import EnrollmentDto
from api.application.dto.academic_record_dto import SubjectRecordDto
from api.application.dto.tool_result import ToolResult
from api.application.page import FIRST_PAGE, PageRequest
from api.domain.brand import Modality
from api.domain.ontology import academic_enrollment, academic_performance, limits, overview
from api.presentation.tools.registry import ToolRegistry


class AcademicTools:
    def __init__(self, service: AcademicService) -> None:
        self._service = service

    @ToolRegistry.declares(
        academic_enrollment.DATA_DE_REFERENCIA,
        academic_enrollment.CALENDARIO_2027,
        overview.PERIODO_COBERTO,
    )
    async def get_academic_calendar(
        self, term: str | None = None
    ) -> ToolResult[AcademicCalendarDto]:
        """Mostra as datas de um semestre e o último cadastrado.

        Use para saber o semestre atual, quando começam as AVs ou quando o semestre termina.
        """
        return await self._service.get_academic_calendar(term)

    @ToolRegistry.declares(academic_enrollment.OFERTA)
    async def list_course_offers(
        self,
        course: str | None = None,
        modality: Modality | None = None,
        unit: str | None = None,
        page: PageRequest = FIRST_PAGE,
    ) -> ToolResult[list[CourseOfferDto]]:
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
        enrollment: str | None = None,
        semester: int | None = None,
        subject: str | None = None,
        *,
        pending_only: bool = False,
        page: PageRequest = FIRST_PAGE,
    ) -> ToolResult[list[CurriculumSubjectDto]]:
        """Mostra a matriz do aluno com a situação em cada disciplina.

        Use para disciplinas por semestre, pré-requisitos, TCC, estágio ou o que falta.
        """
        return await self._service.get_curriculum(
            enrollment, semester, subject, pending_only=pending_only, page=page
        )

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
        enrollment: str | None = None,
        term: str | None = None,
        subject: str | None = None,
        page: PageRequest = FIRST_PAGE,
    ) -> ToolResult[list[SubjectRecordDto]]:
        """Lista as disciplinas cursadas com notas, frequência e resultado.

        Use para ver o semestre atual, uma nota, uma reprovação ou a nota necessária na AV2.
        """
        return await self._service.list_subject_records(enrollment, term, subject, page)

    @ToolRegistry.declares(limits.DADOS_INTERNOS)
    async def list_subject_professors(
        self, subject: str, term: str | None = None
    ) -> ToolResult[list[SubjectProfessorDto]]:
        """Lista quem leciona uma disciplina em um semestre, na instituição do aluno.

        Use para saber quem é o professor e como contatá-lo.
        """
        return await self._service.list_subject_professors(subject, term)
