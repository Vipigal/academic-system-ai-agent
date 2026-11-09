from collections.abc import Callable
from typing import Final

from sqlalchemy import ColumnElement

from api.domain.identity.session import StudentSession
from api.persistence.core.base import Base


class OwnershipError(Exception):
    pass


PUBLIC: Final = None

type OwnerClause = Callable[[StudentSession], ColumnElement[bool]]
type OwnershipRule = OwnerClause | None
type OwnershipMap = dict[type[Base], OwnershipRule]
