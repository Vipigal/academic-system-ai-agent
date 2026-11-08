from pydantic import BaseModel, ConfigDict


class DevStudentDto(BaseModel):
    model_config = ConfigDict(frozen=True)

    brand: str
    student_id: str
    full_name: str
    status: str
