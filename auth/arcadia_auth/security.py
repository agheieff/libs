from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Optional

from jose import jwt, JWTError
from passlib.context import CryptContext


# Password hashing context: prefer argon2id when available, fallback to PBKDF2
try:
    pwd_context = CryptContext(schemes=["argon2", "pbkdf2_sha256"], deprecated="auto")
except Exception:
    # Environments without argon2 deps will still work with PBKDF2
    pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")


def set_password_context(context: CryptContext) -> None:
    """Allow applications to replace the CryptContext at runtime."""
    global pwd_context
    pwd_context = context


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, password_hash: str) -> bool:
    try:
        return pwd_context.verify(plain_password, password_hash)
    except Exception:
        return False


def create_access_token(subject: str | int, secret_key: str, algorithm: str = "HS256", expires_minutes: int = 60 * 24 * 7) -> str:
    now = datetime.now(timezone.utc)
    exp = now + timedelta(minutes=expires_minutes)
    payload = {"sub": str(subject), "iat": int(now.timestamp()), "exp": int(exp.timestamp())}
    return jwt.encode(payload, secret_key, algorithm=algorithm)


def decode_token(token: str, secret_key: str, algorithms: list[str] = ["HS256"]) -> Optional[dict]:
    try:
        return jwt.decode(token, secret_key, algorithms=algorithms)
    except JWTError:
        return None
