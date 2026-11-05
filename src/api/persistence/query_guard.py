from collections.abc import Iterator

from sqlalchemy import BinaryExpression, Column, ColumnClause, FromClause, Join, Select, Table
from sqlalchemy.sql import visitors
from sqlalchemy.sql.elements import (
    BindParameter,
    BooleanClauseList,
    ClauseList,
    ExpressionClauseList,
    Grouping,
    Null,
    UnaryExpression,
)
from sqlalchemy.sql.functions import FunctionElement
from sqlalchemy.sql.operators import custom_op

from api.persistence.ownership import OwnershipError

ALLOWED_ELEMENTS = (
    BindParameter,
    BooleanClauseList,
    ClauseList,
    ExpressionClauseList,
    Grouping,
    Join,
    Null,
    Table,
)
ALLOWED_FUNCTIONS = frozenset({"coalesce", "count", "lower", "max", "min", "sum", "upper"})
STATEMENT_ATTRIBUTES_WITH_FREE_SQL = (
    "_hints",
    "_independent_ctes",
    "_prefixes",
    "_statement_hints",
    "_suffixes",
    "_with_options",
)
COUNT_ALL_COLUMNS = "*"


class QueryGuard:
    @classmethod
    def reject_unsafe_constructs(cls, stmt: object) -> None:
        if not isinstance(stmt, Select):
            message = f"o adapter só aceita select simples, recebeu {type(stmt).__name__}"
            raise OwnershipError(message)
        cls._reject_free_sql(stmt)
        for root in (stmt, *stmt.get_final_froms()):
            cls._reject_elements_outside_the_allowlist(root, stmt)

    @classmethod
    def tables_in[RowT](cls, stmt: Select[RowT]) -> list[FromClause]:
        return [table for source in stmt.get_final_froms() for table in cls._tables_of(source)]

    @staticmethod
    def _reject_free_sql(stmt: object) -> None:
        for attribute in STATEMENT_ATTRIBUTES_WITH_FREE_SQL:
            if getattr(stmt, attribute):
                message = f"construção não aceita pelo adapter: {attribute}"
                raise OwnershipError(message)

    @classmethod
    def _reject_elements_outside_the_allowlist(
        cls, root: visitors.ExternallyTraversible, stmt: object
    ) -> None:
        for element in visitors.iterate(root):
            if element is not stmt and not cls._is_allowed(element):
                message = f"construção não aceita pelo adapter: {type(element).__name__}"
                raise OwnershipError(message)

    @classmethod
    def _is_allowed(cls, element: visitors.ExternallyTraversible) -> bool:
        if isinstance(element, FunctionElement):
            return element.name in ALLOWED_FUNCTIONS and not element.packagenames
        if isinstance(element, BinaryExpression | UnaryExpression):
            return not isinstance(element.operator, custom_op)
        if isinstance(element, ColumnClause):
            return cls._is_table_column(element)
        return isinstance(element, ALLOWED_ELEMENTS)

    @staticmethod
    def _is_table_column(element: ColumnClause[object]) -> bool:
        if element.is_literal:
            return element.name == COUNT_ALL_COLUMNS
        return isinstance(element, Column) and element.table is not None

    @classmethod
    def _tables_of(cls, source: FromClause) -> Iterator[FromClause]:
        if isinstance(source, Join):
            yield from cls._tables_of(source.left)
            yield from cls._tables_of(source.right)
        elif isinstance(source, Table):
            yield source
        else:
            message = f"origem não aceita pelo adapter: {type(source).__name__}"
            raise OwnershipError(message)
