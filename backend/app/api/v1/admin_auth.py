from fastapi import APIRouter, Depends, HTTPException, Request, Response, status

from app.api.deps import AppSettings, CurrentAdmin, DbSession, get_client_ip, require_csrf
from app.core.rate_limit import get_login_rate_limiter
from app.core.security import (
    CSRF_COOKIE_NAME,
    SESSION_COOKIE_NAME,
    create_session_token,
    generate_csrf_token,
)
from app.schemas.auth import AdminMe, LoginRequest, LoginResponse
from app.services.auth_service import authenticate_admin

router = APIRouter(prefix="/admin/auth", tags=["admin-auth"])


@router.post("/login", response_model=LoginResponse)
def login(payload: LoginRequest, request: Request, response: Response, db: DbSession, settings: AppSettings) -> LoginResponse:
    limiter = get_login_rate_limiter()
    rate_key = f"{get_client_ip(request)}:{payload.email.lower()}"
    if not limiter.is_allowed(rate_key):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many login attempts. Please try again later.",
        )
    limiter.record_attempt(rate_key)

    admin = authenticate_admin(db, email=payload.email, password=payload.password)
    if admin is None:
        db.commit()
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password.")

    limiter.reset(rate_key)
    db.commit()

    session_token = create_session_token(admin.id)
    csrf_token = generate_csrf_token()

    response.set_cookie(
        SESSION_COOKIE_NAME,
        session_token,
        max_age=settings.admin_session_max_age_seconds,
        httponly=True,
        secure=settings.admin_session_cookie_secure,
        samesite="lax",
        path="/",
    )
    response.set_cookie(
        CSRF_COOKIE_NAME,
        csrf_token,
        max_age=settings.admin_session_max_age_seconds,
        httponly=False,
        secure=settings.admin_session_cookie_secure,
        samesite="lax",
        path="/",
    )
    return LoginResponse(csrf_token=csrf_token)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(require_csrf)])
def logout(response: Response, _admin: CurrentAdmin) -> None:
    response.delete_cookie(SESSION_COOKIE_NAME, path="/")
    response.delete_cookie(CSRF_COOKIE_NAME, path="/")


@router.get("/me", response_model=AdminMe)
def me(admin: CurrentAdmin) -> AdminMe:
    return AdminMe(id=admin.id, email=admin.email)
