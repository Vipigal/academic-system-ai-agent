from collections.abc import Collection, Mapping, Sequence

from api.domain.identity.session import EnrollmentKey
from api.domain.lms.account import LmsAccount
from api.persistence.lms.dialect import LmsDialect
from api.persistence.lms.models import LmsUserRow
from api.persistence.sag.dialect import SagDialect

type AccountKey = tuple[str, str]
type UserIndex = Mapping[AccountKey, LmsUserRow]


class AccountMapper:
    @classmethod
    def to_entities(
        cls, users: Sequence[LmsUserRow], enrollment_keys: Collection[EnrollmentKey]
    ) -> list[LmsAccount]:
        by_key = {cls._key_of(user): user for user in users}
        ordered = sorted(enrollment_keys, key=lambda key: (key.source_brand, key.student_id))
        return [cls._account(key, by_key) for key in ordered]

    @staticmethod
    def _key_of(user: LmsUserRow) -> AccountKey:
        return user.tenant_id, (user.student_id or "").strip().upper()

    @staticmethod
    def _account(key: EnrollmentKey, by_key: UserIndex) -> LmsAccount:
        reference = SagDialect.reference(key.source_brand, key.student_id)
        user = by_key.get(LmsDialect.account_key(key.ref))
        if user is None:
            return LmsAccount.missing(reference)
        return LmsAccount(
            enrollment=reference,
            exists=True,
            suspended=user.suspended,
            last_access=user.last_access,
        )
