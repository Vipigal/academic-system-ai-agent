from collections.abc import Sequence
from typing import Protocol

from api.domain.invoice import Invoice


class InvoiceRepository(Protocol):
    async def list_all(self) -> Sequence[Invoice]: ...
