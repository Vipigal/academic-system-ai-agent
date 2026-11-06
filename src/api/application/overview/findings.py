from dataclasses import dataclass

from api.application.overview.dto.pending import AttentionItemDto, PendingArea
from api.application.shared.tool_result import Caveat

type Found = dict[PendingArea, list[AttentionItemDto]]


@dataclass(frozen=True, slots=True)
class Findings:
    found: Found
    caveats: tuple[Caveat, ...]
