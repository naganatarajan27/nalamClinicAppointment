from datetime import date, timedelta


def _next_weekday(target_weekday: int) -> date:
    """target_weekday: 0=Monday .. 6=Sunday"""
    today = date.today()
    days_ahead = (target_weekday - today.weekday()) % 7
    days_ahead = days_ahead or 7  # always a future date, never today
    return today + timedelta(days=days_ahead)


def test_availability_empty_when_no_schedule_configured(client, doctor):
    on_date = _next_weekday(0)
    response = client.get(
        "/api/v1/availability", params={"doctor_id": str(doctor.id), "date": on_date.isoformat()}
    )
    assert response.status_code == 200
    assert response.json()["available_times"] == []


def test_admin_can_configure_and_see_availability(client, doctor, auth_headers):
    create = client.post(
        f"/api/v1/admin/doctors/{doctor.id}/availability",
        json={"day_of_week": 0, "start_time": "09:00:00", "end_time": "10:00:00", "slot_duration_minutes": 30},
        headers=auth_headers,
    )
    assert create.status_code == 201
    body = create.json()
    assert body["day_of_week"] == 0
    assert body["slot_duration_minutes"] == 30

    listed = client.get(f"/api/v1/admin/doctors/{doctor.id}/availability", headers=auth_headers)
    assert listed.status_code == 200
    assert len(listed.json()) == 1


def test_configured_availability_produces_public_slots(client, doctor, auth_headers):
    client.post(
        f"/api/v1/admin/doctors/{doctor.id}/availability",
        json={"day_of_week": 0, "start_time": "09:00:00", "end_time": "10:00:00", "slot_duration_minutes": 30},
        headers=auth_headers,
    )
    on_date = _next_weekday(0)

    response = client.get(
        "/api/v1/availability", params={"doctor_id": str(doctor.id), "date": on_date.isoformat()}
    )
    assert response.status_code == 200
    assert response.json()["available_times"] == ["09:00:00", "09:30:00"]


def test_availability_create_rejects_start_after_end(client, doctor, auth_headers):
    response = client.post(
        f"/api/v1/admin/doctors/{doctor.id}/availability",
        json={"day_of_week": 1, "start_time": "10:00:00", "end_time": "09:00:00"},
        headers=auth_headers,
    )
    assert response.status_code == 422


def test_availability_requires_authentication(client, doctor):
    # The CSRF check runs before the auth check for this CSRF-protected route
    # (same ordering as the existing admin-appointments routes), so an
    # anonymous request is rejected for a missing CSRF token, not a missing
    # session.
    response = client.post(
        f"/api/v1/admin/doctors/{doctor.id}/availability",
        json={"day_of_week": 1, "start_time": "09:00:00", "end_time": "10:00:00"},
    )
    assert response.status_code == 403

    listing = client.get(f"/api/v1/admin/doctors/{doctor.id}/availability")
    assert listing.status_code == 401


def test_availability_update_and_delete(client, doctor, auth_headers):
    create = client.post(
        f"/api/v1/admin/doctors/{doctor.id}/availability",
        json={"day_of_week": 2, "start_time": "09:00:00", "end_time": "12:00:00"},
        headers=auth_headers,
    )
    availability_id = create.json()["id"]

    update = client.patch(
        f"/api/v1/admin/doctors/{doctor.id}/availability/{availability_id}",
        json={"is_active": False},
        headers=auth_headers,
    )
    assert update.status_code == 200
    assert update.json()["is_active"] is False

    delete = client.delete(
        f"/api/v1/admin/doctors/{doctor.id}/availability/{availability_id}", headers=auth_headers
    )
    assert delete.status_code == 204

    listed = client.get(f"/api/v1/admin/doctors/{doctor.id}/availability", headers=auth_headers)
    assert listed.json() == []
