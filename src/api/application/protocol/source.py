import asyncio
from collections.abc import Sequence

from api.application.protocol.snapshot import ProtocolSnapshot
from api.domain.ports.clock import Clock
from api.domain.ports.finance import ServiceFeeRepository
from api.domain.ports.protocol import ProtocolRepository
from api.domain.protocol.catalog import Service


class ProtocolSource:
    def __init__(
        self, protocols: ProtocolRepository, fees: ServiceFeeRepository, clock: Clock
    ) -> None:
        self._protocols = protocols
        self._fees = fees
        self._clock = clock

    async def services(self) -> Sequence[Service]:
        return await self._protocols.list_services()

    async def snapshot(self) -> ProtocolSnapshot:
        protocols, fees = await asyncio.gather(
            self._protocols.list_protocols(), self._fees.list_service_fees()
        )
        return ProtocolSnapshot(protocols, fees, self._clock.today())
