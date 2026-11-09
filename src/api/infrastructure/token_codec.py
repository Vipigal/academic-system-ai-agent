import time

import jwt

ALGORITHM = "HS256"
SECONDS_PER_MINUTE = 60
REQUIRED_CLAIMS = ["sub", "exp"]


class JwtCodec:
    def __init__(self, secret: str, ttl_minutes: int) -> None:
        if not secret:
            raise ValueError("the signing secret must not be empty")
        self._secret = secret
        self._ttl_seconds = ttl_minutes * SECONDS_PER_MINUTE

    def issue(self, person_id: str) -> str:
        claims = {"sub": person_id, "exp": int(time.time()) + self._ttl_seconds}
        return jwt.encode(claims, self._secret, algorithm=ALGORITHM)

    def person_of(self, token: str) -> str | None:
        try:
            claims = jwt.decode(
                token,
                self._secret,
                algorithms=[ALGORITHM],
                options={"require": REQUIRED_CLAIMS},
            )
        except jwt.InvalidTokenError:
            return None
        subject = claims["sub"]
        return subject if isinstance(subject, str) and subject else None
