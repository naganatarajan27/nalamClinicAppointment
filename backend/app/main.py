import logging

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.v1.router import api_router
from app.core.config import get_settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("nalam")

settings = get_settings()


def _validate_production_config() -> None:
    if not settings.is_production:
        return
    missing = []
    if settings.session_secret == "replace-with-a-long-random-secret":
        missing.append("SESSION_SECRET")
    if not settings.admin_session_cookie_secure:
        missing.append("ADMIN_SESSION_COOKIE_SECURE=true")
    if settings.database_url.startswith("postgresql") and "password@" in settings.database_url:
        missing.append("DATABASE_URL (still using example credentials)")
    if missing:
        raise RuntimeError(
            "Refusing to start in production with unsafe configuration: " + ", ".join(missing)
        )


_validate_production_config()

app = FastAPI(title=settings.app_name, version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_origin],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "DELETE"],
    allow_headers=["Content-Type", "X-CSRF-Token"],
)


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.exception("Unhandled error processing %s %s", request.method, request.url.path)
    return JSONResponse(status_code=500, content={"detail": "An unexpected error occurred."})


app.include_router(api_router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
