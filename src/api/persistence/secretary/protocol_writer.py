from api.domain.identity.session import EnrollmentKey
from api.domain.protocol.opening import ProtocolOpening
from api.persistence.core.ownership import OwnershipError
from api.persistence.core.repository_adapter import RepositoryAdapter
from api.persistence.sag.dialect import SagDialect
from api.persistence.secretary.opening_mapper import ProtocolOpeningMapper


class SqlProtocolWriter:
    def __init__(self, adapter: RepositoryAdapter) -> None:
        self._adapter = adapter

    async def save(self, opening: ProtocolOpening) -> str:
        key = self._key_of(opening.enrollment_reference)
        session = self._adapter.student_session
        rows = ProtocolOpeningMapper.rows(opening, key.student_id, session.cpf)
        await self._adapter.write(*rows.steps)
        return rows.protocol.id

    def _key_of(self, reference: str) -> EnrollmentKey:
        for key in self._adapter.student_session.enrollment_keys:
            if SagDialect.reference(key.source_brand, key.student_id) == reference:
                return key
        message = "o protocolo só nasce para uma matrícula da sessão"
        raise OwnershipError(message)
