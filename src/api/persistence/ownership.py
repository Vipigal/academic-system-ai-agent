from collections.abc import Callable
from dataclasses import dataclass

from sqlalchemy import ColumnElement, FromClause

from api.domain.session import StudentSession
from api.persistence.base import Base


class OwnershipError(Exception):
    pass


class Public:
    pass


@dataclass(frozen=True, slots=True)
class Via:
    parent: type[Base]
    link: ColumnElement[bool]

    def assert_joined(self, table: FromClause, tables: list[FromClause]) -> None:
        if self.parent.__table__ not in tables:
            parent_name = self.parent.__tablename__
            message = f"{table} exige JOIN com {parent_name}"
            raise OwnershipError(message)


type OwnerClause = Callable[[StudentSession], ColumnElement[bool]]
type OwnershipRule = OwnerClause | Via | Public
