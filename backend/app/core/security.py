import secrets
from dataclasses import dataclass
from uuid import UUID

from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError, InvalidHashError
from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer

from app.core.config import get_settings

_hasher = PasswordHasher()

SESSION_COOKIE_NAME = "nalam_admin_session"
CSRF_COOKIE_NAME = "nalam_csrf_token"
CSRF_HEADER_NAME = "X-CSRF-Token"


def hash_password(plain_password: str) -> str:
    return _hasher.hash(plain_password)


def verify_password(plain_password: str, password_hash: str) -> bool:
    try:
        return _hasher.verify(password_hash, plain_password)
    except (VerifyMismatchError, InvalidHashError):
        return False


@dataclass
class SessionPayload:
    admin_id: str


def _serializer() -> URLSafeTimedSerializer:
    settings = get_settings()
    return URLSafeTimedSerializer(settings.session_secret, salt="nalam-admin-session")


def create_session_token(admin_id: UUID) -> str:
    return _serializer().dumps({"admin_id": str(admin_id)})


def read_session_token(token: str) -> SessionPayload | None:
    settings = get_settings()
    try:
        data = _serializer().loads(token, max_age=settings.admin_session_max_age_seconds)
    except (BadSignature, SignatureExpired):
        return None
    admin_id = data.get("admin_id")
    if not admin_id:
        return None
    return SessionPayload(admin_id=admin_id)


def generate_csrf_token() -> str:
    return secrets.token_urlsafe(32)


def generate_public_reference() -> str:
    return "NAL-" + secrets.token_hex(5).upper()


def generate_confirmation_token() -> str:
    return secrets.token_urlsafe(32)
