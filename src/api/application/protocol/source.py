import asyncio
from collections.abc import Sequence

from api.application.protocol.snapshot import ProtocolSnapshot
from api.domain.academic.enrollment import Enrollment
from api.domain.ports.academic import StudentAcademicRepository
from api.domain.ports.clock import Clock
from api.domain.ports.finance import ServiceFeeRepository
from api.domain.ports.protocol import ProtocolRepository
from api.domain.protocol.catalog import Service


class ProtocolSource:
    def __init__(
        self,
        protocols: ProtocolRepository,
        fees: ServiceFeeRepository,
        academic: StudentAcademicRepository,
        clock: Clock,
    ) -> None:
        self._protocols = protocols
        self._fees = fees
        self._academic = academic
        self._clock = clock

    async def services(self) -> tuple[Sequence[Service], Sequence[Enrollment]]:
        return await asyncio.gather(
            self._protocols.list_services(), self._academic.list_enrollments()
        )

    async def snapshot(self) -> ProtocolSnapshot:
        protocols, fees = await asyncio.gather(
            self._protocols.list_protocols(), self._fees.list_service_fees()
        )
        return ProtocolSnapshot(protocols, fees, self._clock.today())
