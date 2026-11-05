from api.application.protocol_service import ProtocolService


class ProtocolTools:
    def __init__(self, service: ProtocolService) -> None:
        self._service = service
