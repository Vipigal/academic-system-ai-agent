from api.application.academic_service import AcademicService


class AcademicTools:
    def __init__(self, service: AcademicService) -> None:
        self._service = service
