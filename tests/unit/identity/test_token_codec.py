import secrets

import jwt
import pytest

from api.infrastructure.token_codec import JwtCodec

SECRET = secrets.token_urlsafe(32)


def test_round_trips_the_person() -> None:
    codec = JwtCodec(SECRET, 5)
    assert codec.person_of(codec.issue("3000003")) == "3000003"


def test_rejects_a_token_signed_with_another_secret() -> None:
    token = JwtCodec(secrets.token_urlsafe(32), 5).issue("3000003")
    assert JwtCodec(SECRET, 5).person_of(token) is None


def test_rejects_an_expired_token() -> None:
    codec = JwtCodec(SECRET, -1)
    assert codec.person_of(codec.issue("3000003")) is None


def test_rejects_an_unsigned_token() -> None:
    token = jwt.encode({"sub": "3000003", "exp": 4102444800}, key=None, algorithm="none")
    assert JwtCodec(SECRET, 5).person_of(token) is None


def test_rejects_a_token_without_expiry() -> None:
    token = jwt.encode({"sub": "3000003"}, SECRET, algorithm="HS256")
    assert JwtCodec(SECRET, 5).person_of(token) is None


def test_rejects_garbage() -> None:
    assert JwtCodec(SECRET, 5).person_of("not-a-token") is None


def test_refuses_an_empty_secret() -> None:
    with pytest.raises(ValueError, match="secret"):
        JwtCodec("", 5)
