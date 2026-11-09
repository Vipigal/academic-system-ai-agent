from uuid import UUID

from pydantic import BaseModel, ConfigDict


class ConversationDto(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: UUID
