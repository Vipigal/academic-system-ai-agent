from api.application.lms_service import LmsService


class LmsTools:
    def __init__(self, service: LmsService) -> None:
        self._service = service
