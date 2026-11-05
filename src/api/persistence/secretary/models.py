from sqlalchemy.orm import Mapped, mapped_column

from api.persistence.base import Base

SECRETARY_SCHEMA = {"schema": "secretary"}


class ProtocolRow(Base):
    __tablename__ = "protocol"
    __table_args__ = SECRETARY_SCHEMA

    id: Mapped[str] = mapped_column("protocol", primary_key=True)
