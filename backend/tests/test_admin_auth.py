from tests.conftest import ADMIN_EMAIL, ADMIN_PASSWORD


def test_admin_apis_require_authentication(client):
    response = client.get("/api/v1/admin/appointments")
    assert response.status_code == 401


def test_login_with_unknown_email_and_wrong_password_return_same_generic_error(client, admin_user):
    unknown = client.post(
        "/api/v1/admin/auth/login", json={"email": "nobody@nalamclinic.com", "password": "whatever123"}
    )
    wrong_password = client.post(
        "/api/v1/admin/auth/login", json={"email": ADMIN_EMAIL, "password": "wrong-password"}
    )
    assert unknown.status_code == 401
    assert wrong_password.status_code == 401
    assert unknown.json()["detail"] == wrong_password.json()["detail"]


def test_successful_login_sets_session_and_allows_me(client, admin_user):
    login = client.post("/api/v1/admin/auth/login", json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD})
    assert login.status_code == 200
    assert "csrf_token" in login.json()

    me = client.get("/api/v1/admin/auth/me")
    assert me.status_code == 200
    assert me.json()["email"] == ADMIN_EMAIL


def test_logout_requires_csrf_header(client, admin_user):
    client.post("/api/v1/admin/auth/login", json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD})

    missing_csrf = client.post("/api/v1/admin/auth/logout")
    assert missing_csrf.status_code == 403


def test_logout_clears_session(client, admin_user, auth_headers):
    logout = client.post("/api/v1/admin/auth/logout", headers=auth_headers)
    assert logout.status_code == 204

    me = client.get("/api/v1/admin/auth/me")
    assert me.status_code == 401


def test_login_rate_limited_after_repeated_failures(client, admin_user):
    from app.core.rate_limit import get_login_rate_limiter

    get_login_rate_limiter().reset(f"testclient:{ADMIN_EMAIL.lower()}")

    last_status = None
    for _ in range(10):
        resp = client.post(
            "/api/v1/admin/auth/login", json={"email": ADMIN_EMAIL, "password": "wrong-password"}
        )
        last_status = resp.status_code
    assert last_status == 429
