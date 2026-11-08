from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class DevStudent:
    brand: str
    student_id: str
    full_name: str
    status: str
