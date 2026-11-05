from dataclasses import dataclass, field

from api.domain.brand import Brand


@dataclass(frozen=True, slots=True)
class StudentSession:
    person_ids: frozenset[str]
    cpf: str = field(repr=False)
    enrollment_keys: frozenset[tuple[str, str]]
    brands: frozenset[Brand]
    contract_ids: frozenset[str]
    self_paid_contract_ids: frozenset[str]
    company_paid_contract_ids: frozenset[str]
    lms_user_ids: frozenset[str]
    protocol_ids: frozenset[str]
