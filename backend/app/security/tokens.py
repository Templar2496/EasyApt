import time

import jwt

from ..core.settings import settings


def create_access(
    sub: str, roles: list[str] | None = None, ttl: int | None = None
) -> str:
    now = int(time.time())
    exp = now + (ttl or settings.JWT_TTL_SECONDS)
    return jwt.encode(
        {"iss": "easyapt", "sub": sub, "roles": roles or [], "iat": now, "exp": exp},
        settings.JWT_SECRET,
        algorithm="HS256",
    )
