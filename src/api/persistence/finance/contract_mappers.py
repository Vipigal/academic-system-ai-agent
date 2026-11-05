from collections import defaultdict
from collections.abc import Iterable, Sequence
from datetime import date
from decimal import Decimal

from api.domain.finance_agreement import Agreement
from api.domain.finance_contract import Contract, PayerType, Scholarship
from api.domain.invoice import Invoice
from api.domain.money import Money
from api.persistence.brasilia import BrasiliaTime
from api.persistence.finance.charge_models import AgreementRow, DiscountRow
from api.persistence.finance.labels import FinanceLabels
from api.persistence.finance.models import ContractRow


class ContractMapper:
    @classmethod
    def to_entities(
        cls,
        rows: Iterable[ContractRow],
        discounts: Iterable[DiscountRow],
        self_paid: frozenset[str],
        company_paid: frozenset[str],
    ) -> Sequence[Contract]:
        scholarships: defaultdict[str, list[Scholarship]] = defaultdict(list)
        for discount in discounts:
            scholarships[discount.contract_id].append(cls._scholarship(discount))
        return [
            Contract(
                id=row.id,
                course_code=row.product_code,
                situation=FinanceLabels.contract_situation(row.status),
                payer=cls._payer(row, self_paid, company_paid),
                scholarships=tuple(scholarships[row.id]),
            )
            for row in rows
        ]

    @staticmethod
    def _payer(
        row: ContractRow, self_paid: frozenset[str], company_paid: frozenset[str]
    ) -> PayerType:
        if row.id in self_paid:
            return PayerType.SELF
        if row.id in company_paid:
            return PayerType.COMPANY
        return PayerType.OTHER_PERSON

    @staticmethod
    def _scholarship(row: DiscountRow) -> Scholarship:
        return Scholarship(
            id=row.id,
            contract_id=row.contract_id,
            kind=row.kind,
            rate=Decimal(row.rate),
            valid_from=date.fromisoformat(row.valid_from),
            valid_to=date.fromisoformat(row.valid_to) if row.valid_to else None,
        )


class AgreementMapper:
    @staticmethod
    def to_entities(
        rows: Iterable[AgreementRow], invoices: Iterable[Invoice]
    ) -> Sequence[Agreement]:
        installments: defaultdict[str | None, list[Invoice]] = defaultdict(list)
        for invoice in invoices:
            installments[invoice.agreement_id].append(invoice)
        return [
            Agreement(
                id=row.id,
                contract_id=row.contract_id,
                status=FinanceLabels.agreement_status(row.status),
                created_at=BrasiliaTime.from_utc(row.created_at),
                original_debt=Money.from_cents(int(row.original_debt_cents)),
                waived=Money.from_cents(int(row.waived_cents)),
                agreed=Money.from_cents(int(row.agreed_cents)),
                installments=tuple(installments[row.id]),
            )
            for row in rows
        ]
