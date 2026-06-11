import hashlib
import hmac

from codereview.web.security import verify_signature

SECRET = "test-secret"
BODY = b'{"action":"opened"}'


def sign(secret: str, body: bytes) -> str:
    return "sha256=" + hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()


def test_valid_signature():
    assert verify_signature(SECRET, BODY, sign(SECRET, BODY)) is True


def test_invalid_signature():
    assert verify_signature(SECRET, BODY, sign("wrong-secret", BODY)) is False


def test_missing_header():
    assert verify_signature(SECRET, BODY, None) is False


def test_malformed_header():
    assert verify_signature(SECRET, BODY, "sha1=abcdef") is False


def test_tampered_body():
    sig = sign(SECRET, BODY)
    assert verify_signature(SECRET, BODY + b"x", sig) is False
