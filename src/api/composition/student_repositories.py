from dataclasses import dataclass
from typing import Self

from api.persistence.finance.repositories import SqlFinanceRepository
from api.persistence.lms.lms_repository import SqlLmsRepository
from api.persistence.repository_adapter import RepositoryAdapter
from api.persistence.sag.academic_catalog_repository import SagAcademicCatalogRepository
from api.persistence.sag.academic_student_repository import SagStudentAcademicRepository
from api.persistence.secretary.protocol_repository import SqlProtocolRepository


@dataclass(frozen=True, slots=True)
class StudentRepositories:
    academic_catalog: SagAcademicCatalogRepository
    academic_student: SagStudentAcademicRepository
    finance: SqlFinanceRepository
    lms: SqlLmsRepository
    protocols: SqlProtocolRepository

    @classmethod
    def of(cls, adapter: RepositoryAdapter) -> Self:
        return cls(
            academic_catalog=SagAcademicCatalogRepository(adapter),
            academic_student=SagStudentAcademicRepository(adapter),
            finance=SqlFinanceRepository(adapter),
            lms=SqlLmsRepository(adapter),
            protocols=SqlProtocolRepository(adapter),
        )
