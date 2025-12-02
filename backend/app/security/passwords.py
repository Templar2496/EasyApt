from __future__ import annotations

import re

from argon2 import PasswordHasher
from argon2.exceptions import (InvalidHash, VerificationError,
                               VerifyMismatchError)

# Password policy: 12+ chars, upper, lower, digit, special
_POLICY = re.compile(r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[^A-Za-z0-9]).{12,}$")

ph = PasswordHasher()  # argon2id with sensible defaults


def meets_policy(pw: str) -> bool:
    return bool(_POLICY.match(pw))


def hash_password(pw: str) -> str:
    return ph.hash(pw)


def verify_password(pw: str, hashed: str) -> bool:
    """Return True if pw matches hashed Argon2 hash."""
    try:
        # IMPORTANT: (hash, password) order for argon2-cffi
        return ph.verify(hashed, pw)
    except (VerifyMismatchError, VerificationError, InvalidHash):
        return False
