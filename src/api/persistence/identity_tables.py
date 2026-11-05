from sqlalchemy import Column, MetaData, Table, Text

IDENTITY_METADATA = MetaData()

PERSON_CPF = Table(
    "person",
    IDENTITY_METADATA,
    Column("person_id", Text, primary_key=True),
    Column("cpf", Text),
    schema="sag",
)
CONTRACT_PAYER = Table(
    "contract",
    IDENTITY_METADATA,
    Column("contractid", Text, primary_key=True),
    Column("customerid", Text),
    schema="finance",
)
CUSTOMER_TAX_ID = Table(
    "customer",
    IDENTITY_METADATA,
    Column("customerid", Text, primary_key=True),
    Column("taxid", Text),
    schema="finance",
)
PROTOCOL_REQUESTER = Table(
    "protocol",
    IDENTITY_METADATA,
    Column("protocol", Text, primary_key=True),
    Column("stu_id", Text),
    Column("requester_cpf", Text),
    Column("requester_type", Text),
    Column("unit_code", Text),
    schema="secretary",
)
