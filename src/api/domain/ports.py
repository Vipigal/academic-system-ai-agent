from collections.abc import Sequence
from datetime import date
from typing import Protocol

from api.domain.invoice import Invoice


class InvoiceRepository(Protocol):
    async def list_all(self) -> Sequence[Invoice]: ...


class Clock(Protocol):
    def today(self) -> date: ...


class DatabaseProbe(Protocol):
    async def is_available(self) -> bool: ...
