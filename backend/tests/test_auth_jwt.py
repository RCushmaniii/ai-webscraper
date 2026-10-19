"""
JWT verification contract for app.core.auth (PyJWT, since 2026-10-19).

Supabase signs access tokens with ES256 and publishes the public key at
/auth/v1/.well-known/jwks.json. These tests generate a throwaway P-256 key,
serve it as a JWKS, and drive verify_jwt_token through the cases that matter:
a good token is accepted; algorithm confusion, tampering, expiry and a missing
kid are refused; an unknown kid takes the server-side fallback. The rate
limiter's unverified `sub` extraction is covered too, since it moved libraries
in the same change.
"""

import base64
import hashlib
import hmac
import json
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock

import jwt
import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ec
from jwt.algorithms import ECAlgorithm

from app.core import auth
from app.middleware.rate_limiter import _identity_from_request

KID = "test-kid-1"
SUB = "0f6a8c58-7c3e-4b1a-9c0d-1f2e3d4c5b6a"


def _b64url(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode()


@pytest.fixture(scope="module")
def keypair():
    private_key = ec.generate_private_key(ec.SECP256R1())
    public_jwk = ECAlgorithm.to_jwk(private_key.public_key(), as_dict=True)
    public_jwk.update({"kid": KID, "alg": "ES256", "use": "sig"})
    return private_key, public_jwk


@pytest.fixture(autouse=True)
def jwks(monkeypatch, keypair):
    _, public_jwk = keypair

    async def fake_get_jwks():
        return {"keys": [public_jwk]}

    monkeypatch.setattr(auth, "get_jwks", fake_get_jwks)


def make_token(private_key, *, kid=KID, exp_delta=timedelta(hours=1), **claims):
    now = datetime.now(timezone.utc)
    payload = {
        "sub": SUB,
        "email": "user@example.com",
        "role": "authenticated",
        "iat": now,
        "exp": now + exp_delta,
        **claims,
    }
    headers = {"kid": kid} if kid else {}
    return jwt.encode(payload, private_key, algorithm="ES256", headers=headers)


class TestVerifyJwtToken:
    async def test_valid_es256_token_is_accepted(self, keypair):
        private_key, _ = keypair
        payload = await auth.verify_jwt_token(make_token(private_key))
        assert payload["sub"] == SUB
        assert payload["email"] == "user@example.com"

    async def test_hs256_signed_with_public_key_is_rejected(self, keypair):
        """The classic algorithm-confusion attack: an HS256 token whose HMAC
        secret is the server's own public key. Built by hand because PyJWT
        refuses to sign HMAC with key material that looks like a PEM. It must
        fail on the asymmetric algorithm allowlist, before any key is used."""
        private_key, _ = keypair
        public_pem = private_key.public_key().public_bytes(
            serialization.Encoding.PEM, serialization.PublicFormat.SubjectPublicKeyInfo
        )
        now = int(datetime.now(timezone.utc).timestamp())
        header = _b64url(json.dumps({"alg": "HS256", "typ": "JWT", "kid": KID}).encode())
        body = _b64url(json.dumps({"sub": "attacker", "email": "x@y.z", "iat": now, "exp": now + 3600}).encode())
        sig = _b64url(hmac.new(public_pem, f"{header}.{body}".encode(), hashlib.sha256).digest())
        forged = f"{header}.{body}.{sig}"

        assert jwt.get_unverified_header(forged)["alg"] == "HS256"
        with pytest.raises(auth.JWTError):
            await auth.verify_jwt_token(forged)

    async def test_tampered_payload_is_rejected(self, keypair):
        private_key, _ = keypair
        token = make_token(private_key)
        header, _, sig = token.split(".")
        other_payload = make_token(private_key, sub="someone-else").split(".")[1]
        with pytest.raises(auth.JWTError):
            await auth.verify_jwt_token(".".join([header, other_payload, sig]))

    async def test_expired_token_is_rejected(self, keypair):
        private_key, _ = keypair
        with pytest.raises(auth.JWTError):
            await auth.verify_jwt_token(make_token(private_key, exp_delta=timedelta(minutes=-5)))

    async def test_missing_kid_is_rejected(self, keypair):
        private_key, _ = keypair
        with pytest.raises(auth.JWTError):
            await auth.verify_jwt_token(make_token(private_key, kid=None))

    async def test_garbage_token_is_rejected(self):
        with pytest.raises(auth.JWTError):
            await auth.verify_jwt_token("not.a.jwt")

    async def test_wrong_key_signature_is_rejected(self, keypair):
        """Signed by a different P-256 key but claiming our kid."""
        other_key = ec.generate_private_key(ec.SECP256R1())
        with pytest.raises(auth.JWTError):
            await auth.verify_jwt_token(make_token(other_key))

    async def test_unknown_kid_uses_supabase_fallback(self, keypair, monkeypatch):
        private_key, _ = keypair
        fake_user = MagicMock()
        fake_user.user.id = "fallback-user"
        fake_user.user.email = "legacy@example.com"
        fake_user.user.role = "authenticated"
        fake_client = MagicMock()
        fake_client.auth.get_user.return_value = fake_user
        monkeypatch.setattr(auth, "supabase_client", fake_client)

        token = make_token(private_key, kid="legacy-kid")
        payload = await auth.verify_jwt_token(token)
        fake_client.auth.get_user.assert_called_once_with(token)
        assert payload == {"sub": "fallback-user", "email": "legacy@example.com", "role": "authenticated"}

    async def test_unknown_kid_and_failed_fallback_is_rejected(self, keypair, monkeypatch):
        private_key, _ = keypair
        fake_client = MagicMock()
        fake_client.auth.get_user.side_effect = RuntimeError("supabase down")
        monkeypatch.setattr(auth, "supabase_client", fake_client)
        with pytest.raises(auth.JWTError):
            await auth.verify_jwt_token(make_token(private_key, kid="legacy-kid"))


class TestRateLimiterIdentity:
    """The limiter buckets by the UNVERIFIED sub (see _identity_from_request);
    forged tokens are still rejected downstream by get_current_user."""

    def _request(self, headers: dict):
        req = MagicMock()
        req.headers = {k.lower(): v for k, v in headers.items()}
        req.client.host = "203.0.113.9"
        return req

    def test_bearer_sub_becomes_identity(self, keypair):
        private_key, _ = keypair
        token = make_token(private_key)
        assert _identity_from_request(self._request({"Authorization": f"Bearer {token}"})) == (f"user:{SUB}", SUB)

    def test_malformed_bearer_falls_back_to_ip(self):
        req = self._request({"Authorization": "Bearer garbage", "X-Forwarded-For": "198.51.100.7, 10.0.0.1"})
        assert _identity_from_request(req) == ("ip:198.51.100.7", None)

    def test_no_auth_uses_client_ip(self):
        assert _identity_from_request(self._request({})) == ("ip:203.0.113.9", None)
