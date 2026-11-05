from api.application.financial_service import FinancialService


class FinanceTools:
    def __init__(self, service: FinancialService) -> None:
        self._service = service
