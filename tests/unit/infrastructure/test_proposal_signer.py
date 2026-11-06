import secrets

import jwt
import pytest

from api.domain.protocol.proposal import SignedProposal
from api.infrastructure.proposal_signer import ProposalJwtSigner
from api.infrastructure.token_codec import JwtCodec

SECRET = secrets.token_urlsafe(32)
PROPOSAL = SignedProposal(
    person_id="3000003",
    enrollment="UniSaoPaulo:180017",
    service_code="DOC-001",
    message="Preciso de uma declaração",
)


def signer(secret: str = SECRET, ttl_minutes: int = 15) -> ProposalJwtSigner:
    return ProposalJwtSigner(secret, ttl_minutes)


def test_a_signed_proposal_comes_back_whole() -> None:
    assert signer().verify(signer().sign(PROPOSAL)) == PROPOSAL


def flipped(segment: str) -> str:
    replacement = "A" if segment[5] != "A" else "B"
    return segment[:5] + replacement + segment[6:]


def test_any_changed_character_invalidates_the_token() -> None:
    head, payload, signature = signer().sign(PROPOSAL).split(".")
    assert signer().verify(".".join((head, flipped(payload), signature))) is None


def test_an_expired_token_is_refused() -> None:
    assert signer().verify(signer(ttl_minutes=-1).sign(PROPOSAL)) is None


def test_a_token_from_another_secret_is_refused() -> None:
    assert signer().verify(signer(secrets.token_urlsafe(32)).sign(PROPOSAL)) is None


@pytest.mark.parametrize("token", ["", "garbage", "a.b.c"])
def test_garbage_is_refused(token: str) -> None:
    assert signer().verify(token) is None


def test_alg_none_is_refused() -> None:
    claims = {
        "person_id": PROPOSAL.person_id,
        "enrollment": PROPOSAL.enrollment,
        "service_code": PROPOSAL.service_code,
        "message": PROPOSAL.message,
        "exp": 4102444800,
    }
    assert signer().verify(jwt.encode(claims, key="", algorithm="none")) is None


@pytest.mark.parametrize("missing", ["person_id", "enrollment", "service_code", "message", "exp"])
def test_a_token_without_a_claim_is_refused(missing: str) -> None:
    claims = {
        "person_id": "3000003",
        "enrollment": "UniSaoPaulo:180017",
        "service_code": "DOC-001",
        "message": "x",
        "exp": 4102444800,
    }
    del claims[missing]
    assert signer().verify(jwt.encode(claims, SECRET, algorithm="HS256")) is None


def test_a_claim_of_the_wrong_type_is_refused() -> None:
    claims = {
        "person_id": 3000003,
        "enrollment": "UniSaoPaulo:180017",
        "service_code": "DOC-001",
        "message": "x",
        "exp": 4102444800,
    }
    assert signer().verify(jwt.encode(claims, SECRET, algorithm="HS256")) is None


def test_session_and_proposal_tokens_do_not_cross_even_with_the_same_secret() -> None:
    codec = JwtCodec(SECRET, 60)
    assert signer().verify(codec.issue("3000003")) is None
    assert codec.person_of(signer().sign(PROPOSAL)) is None


def test_an_empty_secret_fails_closed() -> None:
    with pytest.raises(ValueError, match="secret"):
        ProposalJwtSigner("", 15)
