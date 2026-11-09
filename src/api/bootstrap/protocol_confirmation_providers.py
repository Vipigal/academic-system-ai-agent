from dishka import Provider, Scope, provide, provide_all

from api.application.protocol.confirmation import ProtocolConfirmation
from api.application.protocol.confirmation_ports import ConfirmationPorts
from api.domain.ports.identity import RequesterDirectory
from api.domain.ports.protocol import ProtocolWriter
from api.persistence.identity.requester_directory import SqlRequesterDirectory
from api.persistence.secretary.protocol_writer import SqlProtocolWriter


class ProtocolConfirmationProvider(Provider):
    scope = Scope.REQUEST

    requesters = provide(SqlRequesterDirectory, provides=RequesterDirectory)
    writer = provide(SqlProtocolWriter, provides=ProtocolWriter)
    confirmation = provide_all(ConfirmationPorts, ProtocolConfirmation)
