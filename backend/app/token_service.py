"""
Token service for secure action links (cancel/reschedule).
Pure Python (stdlib) signed tokens with expiry.

Token format: base64url(payload_json).base64url(signature)
signature = HMAC-SHA256(secret, payload_json_bytes)
"""
from __future__ import annotations

import base64
import hmac
import hashlib
import json
import os
import time
from typing import Any, Dict, Tuple

_ENV_SECRET = "LINK_TOKEN_SECRET"


class TokenError(Exception):
    pass


def _b64url_encode(b: bytes) -> str:
    return base64.urlsafe_b64encode(b).decode("utf-8").rstrip("=")


def _b64url_decode(s: str) -> bytes:
    pad = "=" * (-len(s) % 4)
    return base64.urlsafe_b64decode((s + pad).encode("utf-8"))


def _get_secret() -> bytes:
    secret = os.getenv(_ENV_SECRET)
    if not secret:
        # fallback so dev runs, but you SHOULD set LINK_TOKEN_SECRET in .env
        secret = "dev-only-secret-change-me"
    return secret.encode("utf-8")


def make_token(payload: Dict[str, Any], expires_in_seconds: int = 7 * 24 * 3600) -> str:
    """
    Create a signed token with exp timestamp.
    payload: dict that must be JSON serializable.
    """
    now = int(time.time())
    body = dict(payload)
    body["iat"] = now
    body["exp"] = now + int(expires_in_seconds)

    payload_bytes = json.dumps(body, separators=(",", ":"), sort_keys=True).encode("utf-8")
    sig = hmac.new(_get_secret(), payload_bytes, hashlib.sha256).digest()
    return f"{_b64url_encode(payload_bytes)}.{_b64url_encode(sig)}"


def verify_token(token: str) -> Dict[str, Any]:
    """
    Verify token signature and expiry. Returns payload dict.
    Raises TokenError if invalid/expired.
    """
    try:
        p1, p2 = token.split(".", 1)
    except ValueError as e:
        raise TokenError("Malformed token") from e

    payload_bytes = _b64url_decode(p1)
    sig = _b64url_decode(p2)

    expected = hmac.new(_get_secret(), payload_bytes, hashlib.sha256).digest()
    if not hmac.compare_digest(sig, expected):
        raise TokenError("Invalid token signature")

    payload = json.loads(payload_bytes.decode("utf-8"))
    now = int(time.time())
    exp = int(payload.get("exp", 0))
    if exp <= now:
        raise TokenError("Token expired")

    return payload
