import uuid
from typing import Annotated

from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.core.security import CSRF_COOKIE_NAME, CSRF_HEADER_NAME, SESSION_COOKIE_NAME, read_session_token
from app.db.session import get_db
from app.integrations.email.base import EmailNotificationService
from app.integrations.email.factory import get_email_adapter
from app.integrations.whatsapp.base import WhatsAppNotificationService
from app.integrations.whatsapp.factory import get_whatsapp_adapter
from app.models.admin import Admin
from app.repositories.admin_repository import AdminRepository

DbSession = Annotated[Session, Depends(get_db)]
AppSettings = Annotated[Settings, Depends(get_settings)]


def get_client_ip(request: Request) -> str:
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def get_whatsapp_service() -> WhatsAppNotificationService:
    return get_whatsapp_adapter()


def get_email_service() -> EmailNotificationService:
    return get_email_adapter()


def get_current_admin(request: Request, db: DbSession) -> Admin:
    token = request.cookies.get(SESSION_COOKIE_NAME)
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated.")

    payload = read_session_token(token)
    if payload is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Session expired or invalid.")

    try:
        admin_id = uuid.UUID(payload.admin_id)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated.")

    admin = AdminRepository(db).get(admin_id)
    if admin is None or not admin.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated.")

    return admin


CurrentAdmin = Annotated[Admin, Depends(get_current_admin)]


def require_csrf(request: Request) -> None:
    cookie_token = request.cookies.get(CSRF_COOKIE_NAME)
    header_token = request.headers.get(CSRF_HEADER_NAME)
    if not cookie_token or not header_token or cookie_token != header_token:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Missing or invalid CSRF token.")
