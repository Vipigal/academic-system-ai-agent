from dataclasses import dataclass
from datetime import datetime
from enum import Enum


class DocumentType(Enum):
    DIPLOMA = "diploma"
    COMPLETION_CERTIFICATE = "completion_certificate"
    TRANSCRIPT = "transcript"
    SYLLABUS = "syllabus"
    ENROLLMENT_CERTIFICATE = "enrollment_certificate"


class DocumentDelivery(Enum):
    DIGITAL = "digital"
    PRINTED = "printed"


@dataclass(frozen=True, slots=True)
class ProtocolDocument:
    id: str
    type: DocumentType
    issued_at: datetime
    validation_code: str
    delivery: DocumentDelivery
