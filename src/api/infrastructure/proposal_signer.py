import time

import jwt

from api.domain.protocol.proposal import SignedProposal

ALGORITHM = "HS256"
SECONDS_PER_MINUTE = 60
EXPIRATION = "exp"
PERSON = "person_id"
ENROLLMENT = "enrollment"
SERVICE = "service_code"
REQUIRED_CLAIMS = [PERSON, ENROLLMENT, SERVICE, EXPIRATION]


class ProposalJwtSigner:
    def __init__(self, secret: str, ttl_minutes: int) -> None:
        if not secret:
            raise ValueError("the signing secret must not be empty")
        self._secret = secret
        self._ttl_seconds = ttl_minutes * SECONDS_PER_MINUTE

    def sign(self, proposal: SignedProposal) -> str:
        claims = {
            PERSON: proposal.person_id,
            ENROLLMENT: proposal.enrollment,
            SERVICE: proposal.service_code,
            EXPIRATION: int(time.time()) + self._ttl_seconds,
        }
        return jwt.encode(claims, self._secret, algorithm=ALGORITHM)

    def verify(self, token: str) -> SignedProposal | None:
        try:
            claims = jwt.decode(
                token,
                self._secret,
                algorithms=[ALGORITHM],
                options={"require": REQUIRED_CLAIMS},
            )
        except jwt.InvalidTokenError:
            return None
        return self._proposal_of(claims)

    @staticmethod
    def _proposal_of(claims: dict[str, object]) -> SignedProposal | None:
        person, enrollment = claims[PERSON], claims[ENROLLMENT]
        service = claims[SERVICE]
        if isinstance(person, str) and isinstance(enrollment, str) and isinstance(service, str):
            return SignedProposal(person, enrollment, service)
        return None
