from enum import StrEnum

from pydantic import BaseModel, ConfigDict


class PendingArea(StrEnum):
    ENROLLMENT = "matricula"
    DEBT = "divida"
    UPCOMING_INVOICES = "vencimentos"
    PROTOCOLS = "protocolo"
    ATTENDANCE = "frequencia"
    ONLINE_EXAMS = "prova_online"


class CheckSituation(StrEnum):
    OK = "ok"
    ATTENTION = "attention"


class CheckedItemDto(BaseModel):
    model_config = ConfigDict(frozen=True)

    area: PendingArea
    situation: CheckSituation
    attention_count: int


class AttentionItemDto(BaseModel):
    model_config = ConfigDict(frozen=True)

    area: PendingArea
    reference: str
    detail: dict[str, str]


class PendingItemsDto(BaseModel):
    model_config = ConfigDict(frozen=True)

    reference_date: str
    checked: tuple[CheckedItemDto, ...]
    attention: tuple[AttentionItemDto, ...]
