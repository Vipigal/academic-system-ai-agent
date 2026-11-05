from dataclasses import dataclass
from enum import Enum

STUDENT_NUMBER_LENGTH = 5


class Brand(Enum):
    SAO_PAULO = "sao_paulo"
    MONTANHAS = "montanhas"
    LITORAL = "litoral"
    ATLANTICO = "atlantico"
    ARAUCARIA = "araucaria"


class Modality(Enum):
    IN_PERSON = "in_person"
    ONLINE = "online"


@dataclass(frozen=True, slots=True)
class EnrollmentRef:
    brand: Brand
    modality: Modality
    student_number: str
