from collections.abc import Callable, Sequence
from dataclasses import dataclass

from sqlalchemy import ColumnElement, FromClause, Select

from api.domain.identity.session import StudentSession
from api.persistence.core.base import Base


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


@dataclass(frozen=True, slots=True, eq=False)
class DeclaredQuery[*RowT]:
    root: type[Base]
    build: Callable[[StudentSession], Select[*RowT]]

    def assert_rooted(self, tables: list[FromClause]) -> None:
        if self.root.__table__ not in tables:
            root_name = self.root.__tablename__
            message = f"consulta declarada sem a raiz {root_name}"
            raise OwnershipError(message)


type DeclaredRows[*RowT] = Sequence[tuple[*RowT]]
type OwnerClause = Callable[[StudentSession], ColumnElement[bool]]
type OwnershipRule = OwnerClause | Via | Public
