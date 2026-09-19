import time
import unittest
from uuid import uuid4

import jwt
from cryptography.hazmat.primitives.asymmetric import rsa

from researchguard.auth import AuthenticationError, SupabaseTokenVerifier, bearer_token


class _SigningKey:
    def __init__(self, key):
        self.key = key


class _StaticJwks:
    def __init__(self, key):
        self.key = key

    def get_signing_key_from_jwt(self, _token):
        return _SigningKey(self.key)


class SupabaseTokenTests(unittest.TestCase):
    def setUp(self):
        self.private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        self.public_key = self.private_key.public_key()
        self.issuer = "https://fixture.supabase.co/auth/v1"
        self.user_id = str(uuid4())
        self.verifier = SupabaseTokenVerifier(
            "https://fixture.supabase.co",
            jwks_client=_StaticJwks(self.public_key),
        )

    def token(self, **changes):
        claims = {
            "iss": self.issuer,
            "aud": "authenticated",
            "exp": int(time.time()) + 300,
            "sub": self.user_id,
            "role": "authenticated",
            "email": "researcher@example.test",
        }
        claims.update(changes)
        return jwt.encode(claims, self.private_key, algorithm="RS256", headers={"kid": "fixture-key"})

    def assert_rejected(self, token):
        with self.assertRaisesRegex(AuthenticationError, "invalid or expired"):
            self.verifier.verify(token)

    def test_valid_signature_issuer_expiry_audience_role_and_subject(self):
        user = self.verifier.verify(self.token())
        self.assertEqual(user.user_id, self.user_id)
        self.assertEqual(user.email, "researcher@example.test")

    def test_expired_malformed_tampered_and_wrong_claim_tokens_are_rejected(self):
        self.assert_rejected(self.token(exp=int(time.time()) - 1))
        self.assert_rejected("not-a-jwt")
        token = self.token()
        self.assert_rejected(token[:-1] + ("A" if token[-1] != "A" else "B"))
        self.assert_rejected(self.token(iss="https://attacker.example/auth/v1"))
        self.assert_rejected(self.token(aud="another-service"))
        self.assert_rejected(self.token(role="anon"))
        self.assert_rejected(self.token(sub="browser-supplied-user"))

    def test_unapproved_algorithm_is_rejected_before_key_use(self):
        token = jwt.encode(
            {"iss": self.issuer, "aud": "authenticated", "exp": int(time.time()) + 300,
             "sub": self.user_id, "role": "authenticated"},
            "browser-controlled-secret-with-32-bytes",
            algorithm="HS256",
            headers={"kid": "fixture-key"},
        )
        self.assert_rejected(token)

    def test_bearer_header_parser_is_strict(self):
        self.assertEqual(bearer_token("Bearer abc.def.ghi"), "abc.def.ghi")
        for value in (None, "", "Basic value", "Bearer", "Bearer too many"):
            with self.assertRaises(AuthenticationError):
                bearer_token(value)


if __name__ == "__main__":
    unittest.main()
