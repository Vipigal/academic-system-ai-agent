from dataclasses import dataclass, field

from api.application.chat.rate_limit import ChatRateLimit
from api.domain.identity.session import StudentSession
from api.domain.rate_limit.chat_key import ChatRateLimitKey
from api.domain.rate_limit.decision import RateLimitDecision

DENIED = RateLimitDecision(allowed=False, limit=60, remaining=0, reset_after_seconds=1200)


def session_of(*person_ids: str) -> StudentSession:
    return StudentSession(frozenset(person_ids), "000.000.000-00", frozenset())


@dataclass
class RecordingLimiter:
    decision: RateLimitDecision = DENIED
    keys: list[str] = field(default_factory=list)

    async def consume(self, key: str, /) -> RateLimitDecision:
        self.keys.append(key)
        return self.decision


def test_the_chat_key_is_the_smallest_person_id_of_the_session() -> None:
    session = session_of("3000010", "3000003", "3000007")

    assert ChatRateLimitKey.of(session) == "ratelimit:chat:3000003"


def test_two_logins_of_the_same_person_share_one_key() -> None:
    by_one_enrollment = session_of("3000003", "3000010")
    by_the_other = session_of("3000010", "3000003")

    assert ChatRateLimitKey.of(by_one_enrollment) == ChatRateLimitKey.of(by_the_other)


def test_a_count_within_the_limit_is_allowed_with_what_remains() -> None:
    decision = RateLimitDecision.counted(count=3, limit=5, reset_after_seconds=3500)

    assert decision == RateLimitDecision(
        allowed=True, limit=5, remaining=2, reset_after_seconds=3500
    )
    assert decision.metered


def test_the_last_message_of_the_window_is_allowed_with_nothing_left() -> None:
    assert RateLimitDecision.counted(count=5, limit=5, reset_after_seconds=10).allowed


def test_a_count_over_the_limit_is_denied_and_never_reports_negative_remaining() -> None:
    decision = RateLimitDecision.counted(count=7, limit=5, reset_after_seconds=10)

    assert (decision.allowed, decision.remaining) == (False, 0)


def test_an_unmetered_decision_allows_and_reports_no_quota() -> None:
    decision = RateLimitDecision.unmetered()

    assert decision.allowed
    assert not decision.metered


async def test_the_chat_admission_consumes_the_key_of_the_session_and_returns_the_decision() -> (
    None
):
    limiter = RecordingLimiter()

    decision = await ChatRateLimit(session_of("3000010", "3000003"), limiter).admit()

    assert decision is DENIED
    assert limiter.keys == ["ratelimit:chat:3000003"]
