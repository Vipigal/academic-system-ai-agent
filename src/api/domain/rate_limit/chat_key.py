from api.domain.identity.session import StudentSession

CHAT_PREFIX = "ratelimit:chat:"


class ChatRateLimitKey:
    @staticmethod
    def of(session: StudentSession) -> str:
        return f"{CHAT_PREFIX}{min(session.person_ids)}"
