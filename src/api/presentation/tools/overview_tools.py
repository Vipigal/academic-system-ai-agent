from api.application.overview_service import OverviewService


class OverviewTools:
    def __init__(self, service: OverviewService) -> None:
        self._service = service
