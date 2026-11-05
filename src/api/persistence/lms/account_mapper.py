from collections.abc import Collection, Mapping, Sequence

from api.domain.lms_account import LmsAccount
from api.persistence.lms.dialect import LmsDialect
from api.persistence.lms.models import LmsUserRow
from api.persistence.lms.vocabulary import LmsVocabulary
from api.persistence.sag.dialect import SagDialect

type AccountKey = tuple[str, str]
type UserIndex = Mapping[AccountKey, LmsUserRow]
SUSPENDED = "1"


class AccountMapper:
    @classmethod
    def to_entities(
        cls, users: Sequence[LmsUserRow], enrollment_keys: Collection[tuple[str, str]]
    ) -> list[LmsAccount]:
        by_key = {cls._key_of(user): user for user in users}
        return [cls._account(key, by_key) for key in sorted(enrollment_keys)]

    @staticmethod
    def _key_of(user: LmsUserRow) -> AccountKey:
        return user.tenant_id, (user.student_id or "").strip().upper()

    @staticmethod
    def _account(key: tuple[str, str], by_key: UserIndex) -> LmsAccount:
        reference = SagDialect.reference(*key)
        user = by_key.get(LmsDialect.account_key(SagDialect.enrollment_ref(*key)))
        if user is None:
            return LmsAccount.missing(reference)
        return LmsAccount(
            enrollment=reference,
            exists=True,
            suspended=user.suspended == SUSPENDED,
            last_access=LmsVocabulary.brasilia_or_none(user.last_access),
        )
