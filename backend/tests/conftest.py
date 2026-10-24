import os

os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("SESSION_SECRET", "test-secret-value-not-for-production-use")
os.environ.setdefault("ADMIN_SESSION_COOKIE_SECURE", "false")
os.environ.setdefault("APP_ENV", "test")
os.environ.setdefault("WHATSAPP_PROVIDER", "mock")

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.security import hash_password
from app.db.base import Base
from app.db.session import get_db
from app.main import app
from app.models.admin import Admin
from app.models.doctor import Doctor

ADMIN_EMAIL = "admin@nalamclinic.com"
ADMIN_PASSWORD = "a-strong-test-password-123"


@pytest.fixture(autouse=True)
def _reset_login_rate_limiter():
    """The login rate limiter is a process-global singleton (by design, so it
    survives across requests within a running server); reset it before every
    test so one test's failed-login flood can't 429 a later, unrelated test.
    """
    from app.core.rate_limit import get_login_rate_limiter

    get_login_rate_limiter()._attempts.clear()
    yield


@pytest.fixture()
def db_session():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    testing_session_local = sessionmaker(bind=engine, autocommit=False, autoflush=False)
    session = testing_session_local()
    try:
        yield session
    finally:
        session.close()
        engine.dispose()


@pytest.fixture()
def client(db_session):
    def _override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = _override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture()
def admin_user(db_session):
    admin = Admin(email=ADMIN_EMAIL, password_hash=hash_password(ADMIN_PASSWORD))
    db_session.add(admin)
    db_session.commit()
    return admin


@pytest.fixture()
def doctor(db_session):
    doc = Doctor(display_name="Dr. Asha Rao", specialty="General Medicine", is_active=True)
    db_session.add(doc)
    db_session.commit()
    return doc


@pytest.fixture()
def inactive_doctor(db_session):
    doc = Doctor(display_name="Dr. Retired", specialty="General Medicine", is_active=False)
    db_session.add(doc)
    db_session.commit()
    return doc


@pytest.fixture()
def auth_headers(client, admin_user):
    """Logs the admin in on `client` and returns CSRF headers for mutating requests."""
    response = client.post(
        "/api/v1/admin/auth/login", json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}
    )
    assert response.status_code == 200
    csrf_token = response.json()["csrf_token"]
    return {"X-CSRF-Token": csrf_token}
