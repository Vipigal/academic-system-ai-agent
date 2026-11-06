from sqlalchemy import ColumnElement, Select, case, func, select

from api.domain.finance.contract import PayerType
from api.domain.identity.session import StudentSession
from api.persistence.core.ownership import DeclaredQuery
from api.persistence.finance.labels import COMPANY_CUSTOMER
from api.persistence.finance.models import ContractRow
from api.persistence.identity.tables import CONTRACT_PAYER, CUSTOMER_TAX_ID

PAYER_CONTRACT = CONTRACT_PAYER.alias("payer_contract")


class PayerQueries:
    @staticmethod
    def contracts_with_payer(session: StudentSession) -> Select[ContractRow, str]:
        payer = PayerQueries.payer_of_contract(session.cpf)
        return select(ContractRow, payer).order_by(ContractRow.id)

    @staticmethod
    def payer_of_contract(cpf: str) -> ColumnElement[str]:
        kind = case(
            (CUSTOMER_TAX_ID.c.taxid == cpf, PayerType.SELF.value),
            (CUSTOMER_TAX_ID.c.customertype == COMPANY_CUSTOMER, PayerType.COMPANY.value),
            else_=PayerType.OTHER_PERSON.value,
        )
        found = (
            select(kind)
            .join(PAYER_CONTRACT, PAYER_CONTRACT.c.customerid == CUSTOMER_TAX_ID.c.customerid)
            .where(PAYER_CONTRACT.c.contractid == ContractRow.id)
            .scalar_subquery()
        )
        return func.coalesce(found, PayerType.OTHER_PERSON.value)


CONTRACTS_WITH_PAYER = DeclaredQuery(ContractRow, PayerQueries.contracts_with_payer)
