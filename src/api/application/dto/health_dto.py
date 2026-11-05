from pydantic import BaseModel, ConfigDict


class HealthDto(BaseModel):
    model_config = ConfigDict(frozen=True)

    database_available: bool
