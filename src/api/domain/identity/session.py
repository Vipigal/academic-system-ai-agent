from dataclasses import dataclass, field

from api.domain.shared.brand import Brand, EnrollmentRef


@dataclass(frozen=True, slots=True)
class EnrollmentKey:
    source_brand: str
    student_id: str
    ref: EnrollmentRef


@dataclass(frozen=True, slots=True)
class StudentSession:
    person_ids: frozenset[str]
    cpf: str = field(repr=False)
    enrollment_keys: frozenset[EnrollmentKey]

    @property
    def enrollments(self) -> frozenset[EnrollmentRef]:
        return frozenset(key.ref for key in self.enrollment_keys)

    @property
    def brands(self) -> frozenset[Brand]:
        return frozenset(enrollment.brand for enrollment in self.enrollments)
