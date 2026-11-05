from dataclasses import dataclass

from api.application.dto.overview_pending_dto import AttentionItemDto, PendingArea
from api.application.dto.tool_result import Caveat

type Found = dict[PendingArea, list[AttentionItemDto]]


@dataclass(frozen=True, slots=True)
class Findings:
    found: Found
    caveats: tuple[Caveat, ...]
