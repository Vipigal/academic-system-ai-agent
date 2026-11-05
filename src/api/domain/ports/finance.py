from collections.abc import Mapping, Sequence
from typing import Protocol

from api.domain.finance_agreement import Agreement
from api.domain.finance_contract import Contract
from api.domain.invoice import Invoice


class FinanceRepository(Protocol):
    async def list_invoices(self) -> Sequence[Invoice]: ...

    async def list_contracts(self) -> Sequence[Contract]: ...

    async def list_agreements(self) -> Sequence[Agreement]: ...


class ServiceFeeRepository(Protocol):
    async def list_service_fees(self) -> Mapping[str, Invoice]: ...
