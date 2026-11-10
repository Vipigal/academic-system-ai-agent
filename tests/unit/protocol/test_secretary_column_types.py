from api.domain.shared.money import Money
from api.persistence.secretary.column_types import ServiceFee


def test_the_service_fee_reads_the_currency_text() -> None:
    fee = ServiceFee()
    assert fee.from_source("R$ 150,00") == Money(15000)
    assert fee.to_source(Money(150000)) == "R$ 1.500,00"
