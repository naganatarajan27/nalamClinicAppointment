from datetime import UTC, datetime

from sqlalchemy.orm import Session

from app.core.security import verify_password
from app.models.admin import Admin
from app.repositories.admin_repository import AdminRepository


def authenticate_admin(db: Session, *, email: str, password: str) -> Admin | None:
    repo = AdminRepository(db)
    admin = repo.get_by_email(email)
    if admin is None or not admin.is_active:
        # Still run a hash comparison against a dummy value so that the
        # response time for "unknown email" and "wrong password" is similar,
        # and never reveal which case occurred.
        verify_password(password, "$argon2id$v=19$m=65536,t=3,p=4$c29tZXNhbHQ$ZHVtbXlkdW1teWR1bW15ZHVtbXk")
        return None
    if not verify_password(password, admin.password_hash):
        return None

    admin.last_login_at = datetime.now(UTC)
    db.flush()
    return admin
