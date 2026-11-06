from pydantic import BaseModel, ConfigDict

BEARER = "bearer"


class LoginDto(BaseModel):
    model_config = ConfigDict(frozen=True)

    access_token: str
    token_type: str = BEARER
