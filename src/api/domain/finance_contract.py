from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from enum import Enum


class ContractSituation(Enum):
    ACTIVE = "active"
    SUSPENDED = "suspended"
    TERMINATED = "terminated"
    IN_COLLECTION = "in_collection"


class PayerType(Enum):
    SELF = "self"
    OTHER_PERSON = "other_person"
    COMPANY = "company"


@dataclass(frozen=True, slots=True)
class Scholarship:
    id: str
    contract_id: str
    kind: str
    rate: Decimal
    valid_from: date
    valid_to: date | None

    def is_active_on(self, day: date) -> bool:
        has_ended = self.valid_to is not None and day > self.valid_to
        return self.valid_from <= day and not has_ended


@dataclass(frozen=True, slots=True)
class Contract:
    id: str
    course_code: str
    situation: ContractSituation
    payer: PayerType
    scholarships: tuple[Scholarship, ...]
