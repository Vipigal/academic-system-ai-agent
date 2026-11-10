from dishka import Provider, Scope, provide, provide_all

from api.application.protocol.proposer import ProtocolProposer
from api.application.protocol.queries import ProtocolQueries
from api.application.protocol.service import ProtocolService
from api.application.protocol.source import ProtocolSource
from api.bootstrap.settings import Settings
from api.domain.ports.protocol import ProposalSigner, ProtocolRepository
from api.infrastructure.proposal_signer import ProposalJwtSigner
from api.persistence.secretary.repository import SqlProtocolRepository


class ProtocolProvider(Provider):
    scope = Scope.REQUEST

    protocols = provide(SqlProtocolRepository, provides=ProtocolRepository)
    services = provide_all(ProtocolSource, ProtocolQueries, ProtocolProposer, ProtocolService)

    @provide(scope=Scope.APP)
    def signer(self, settings: Settings) -> ProposalSigner:
        secret = settings.proposal_secret
        return ProposalJwtSigner(
            secret.get_secret_value() if secret else "", settings.proposal_ttl_minutes
        )
