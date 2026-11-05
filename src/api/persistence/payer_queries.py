from collections.abc import Collection

from sqlalchemy import Select, select

from api.persistence.finance.labels import COMPANY_CUSTOMER
from api.persistence.identity_tables import CONTRACT_PAYER, CUSTOMER_TAX_ID


class PayerQueries:
    @staticmethod
    def self_paid_of(cpf: str, contract_ids: Collection[str]) -> Select[str]:
        payer = CUSTOMER_TAX_ID.c.customerid == CONTRACT_PAYER.c.customerid
        own_contract = CONTRACT_PAYER.c.contractid.in_(contract_ids)
        statement = select(CONTRACT_PAYER.c.contractid).join(CUSTOMER_TAX_ID, payer)
        return statement.where(own_contract, CUSTOMER_TAX_ID.c.taxid == cpf)

    @staticmethod
    def company_paid_of(contract_ids: Collection[str]) -> Select[str]:
        payer = CUSTOMER_TAX_ID.c.customerid == CONTRACT_PAYER.c.customerid
        own_contract = CONTRACT_PAYER.c.contractid.in_(contract_ids)
        statement = select(CONTRACT_PAYER.c.contractid).join(CUSTOMER_TAX_ID, payer)
        return statement.where(own_contract, CUSTOMER_TAX_ID.c.customertype == COMPANY_CUSTOMER)
