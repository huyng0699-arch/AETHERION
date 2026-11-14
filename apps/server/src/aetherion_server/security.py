"""Server-side password hashing, opaque session tokens, and subject authorization."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
import hashlib
import hmac
import os
import secrets
from typing import Sequence

DEFAULT_SESSION_TTL_SECONDS = 3600
VALID_ROLES = frozenset({"crew", "operator", "flight_surgeon", "admin"})


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def utc_now_iso() -> str:
    return utc_now().isoformat()


def hash_password(password: str, *, salt_hex: str | None = None) -> str:
    if not password or len(password) < 8:
        raise ValueError("Password must be at least 8 characters long")
    salt = bytes.fromhex(salt_hex) if salt_hex else os.urandom(16)
    derived = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 200_000)
    return f"pbkdf2_sha256$200000${salt.hex()}${derived.hex()}"


def verify_password(password: str, stored_hash: str) -> bool:
    if not password or not stored_hash:
        return False
    parts = stored_hash.split("$")
    if len(parts) != 4 or parts[0] != "pbkdf2_sha256":
        return False
    try:
        iterations = int(parts[1])
        salt = bytes.fromhex(parts[2])
        expected = bytes.fromhex(parts[3])
    except ValueError:
        return False
    derived = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, iterations)
    return hmac.compare_digest(derived, expected)


def generate_session_token() -> str:
    return secrets.token_urlsafe(32)


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def compute_expiry_iso(ttl_seconds: int | None = None, *, now: datetime | None = None) -> str:
    ttl = DEFAULT_SESSION_TTL_SECONDS if ttl_seconds is None else ttl_seconds
    if ttl <= 0:
        raise ValueError("Session TTL must be positive")
    base = now or utc_now()
    return (base + timedelta(seconds=ttl)).isoformat()


def is_expired(expires_at_iso: str, *, now: datetime | None = None) -> bool:
    current = now or utc_now()
    expires_at = datetime.fromisoformat(expires_at_iso)
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    return current >= expires_at


def is_subject_authorized(role: str, allowed_subjects: Sequence[str], subject_id: str) -> bool:
    if role in {"admin", "flight_surgeon", "operator"} and "*" in allowed_subjects:
        return True
    return subject_id in allowed_subjects
