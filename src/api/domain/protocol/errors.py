from api.domain.protocol.proposal import RefusalReason


class ProposalNotFoundError(Exception):
    pass


class DuplicateProtocolError(Exception):
    pass


class ServiceNotOpenableError(Exception):
    def __init__(self, reason: RefusalReason) -> None:
        super().__init__(reason.value)
        self.reason = reason
