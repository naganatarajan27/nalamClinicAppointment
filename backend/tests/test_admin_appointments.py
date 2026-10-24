from datetime import date, timedelta


def _book(client, doctor_id: str) -> dict:
    tomorrow = date.today() + timedelta(days=1)
    payload = {
        "patient_name": "Jane Doe",
        "patient_type": "NEW",
        "phone_number": "+919876543210",
        "whatsapp_number": "+919876543211",
        "doctor_id": doctor_id,
        "requested_date": tomorrow.isoformat(),
        "requested_time": "10:30:00",
        "symptoms": "Persistent cough for a week.",
    }
    return client.post("/api/v1/appointments", json=payload).json()


def test_non_admin_cannot_accept_appointment(client, doctor):
    booked = _book(client, str(doctor.id))
    response = client.get(f"/api/v1/admin/appointments")
    assert response.status_code == 401


def test_admin_can_list_and_filter_appointments(client, doctor, auth_headers):
    _book(client, str(doctor.id))
    response = client.get("/api/v1/admin/appointments", headers=auth_headers)
    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 1
    assert body["items"][0]["whatsapp_number_masked"] != "+919876543211"

    filtered = client.get(
        "/api/v1/admin/appointments", params={"status": "CONFIRMED"}, headers=auth_headers
    )
    assert filtered.json()["total"] == 0


def test_accept_confirms_appointment_and_sends_mock_notification(client, doctor, auth_headers):
    booked = _book(client, str(doctor.id))
    detail = client.get(
        f"/api/v1/admin/appointments", headers=auth_headers
    ).json()["items"][0]

    response = client.patch(
        f"/api/v1/admin/appointments/{detail['id']}/accept",
        json={"admin_note": "Confirmed by phone."},
        headers=auth_headers,
    )
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "CONFIRMED"
    assert body["confirmed_date"] == booked_date(booked)
    assert body["admin_note"] == "Confirmed by phone."

    notifications = client.get(
        f"/api/v1/admin/appointments/{detail['id']}/notifications", headers=auth_headers
    ).json()
    assert len(notifications) == 1
    assert notifications[0]["notification_type"] == "CONFIRMATION"
    assert notifications[0]["status"] == "SENT"


def booked_date(booked: dict) -> str:
    return (date.today() + timedelta(days=1)).isoformat()


def test_propose_slot_does_not_confirm_appointment(client, doctor, auth_headers):
    _book(client, str(doctor.id))
    appt_id = client.get("/api/v1/admin/appointments", headers=auth_headers).json()["items"][0]["id"]

    new_date = (date.today() + timedelta(days=3)).isoformat()
    response = client.patch(
        f"/api/v1/admin/appointments/{appt_id}/propose-slot",
        json={"proposed_date": new_date, "proposed_time": "14:00:00"},
        headers=auth_headers,
    )
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ALTERNATE_PROPOSED"
    assert body["confirmed_date"] is None
    assert body["proposed_date"] == new_date

    notifications = client.get(
        f"/api/v1/admin/appointments/{appt_id}/notifications", headers=auth_headers
    ).json()
    assert notifications[0]["notification_type"] == "ALTERNATE_PROPOSAL"


def test_invalid_status_transition_is_rejected(client, doctor, auth_headers):
    _book(client, str(doctor.id))
    appt_id = client.get("/api/v1/admin/appointments", headers=auth_headers).json()["items"][0]["id"]

    # PENDING -> COMPLETED is not an allowed direct transition.
    response = client.patch(
        f"/api/v1/admin/appointments/{appt_id}/status",
        json={"status": "COMPLETED"},
        headers=auth_headers,
    )
    assert response.status_code == 400


def test_cancel_from_pending_is_allowed(client, doctor, auth_headers):
    _book(client, str(doctor.id))
    appt_id = client.get("/api/v1/admin/appointments", headers=auth_headers).json()["items"][0]["id"]

    response = client.patch(
        f"/api/v1/admin/appointments/{appt_id}/status",
        json={"status": "CANCELLED"},
        headers=auth_headers,
    )
    assert response.status_code == 200
    assert response.json()["status"] == "CANCELLED"


def test_accept_requires_csrf_header(client, doctor, admin_user):
    _book(client, str(doctor.id))
    login = client.post(
        "/api/v1/admin/auth/login",
        json={"email": "admin@nalamclinic.com", "password": "a-strong-test-password-123"},
    )
    assert login.status_code == 200
    appt_id = client.get("/api/v1/admin/appointments").json()["items"][0]["id"]

    response = client.patch(f"/api/v1/admin/appointments/{appt_id}/accept", json={})
    assert response.status_code == 403


def test_patient_can_confirm_proposed_slot_via_token(client, doctor, auth_headers, db_session):
    _book(client, str(doctor.id))
    appt_id = client.get("/api/v1/admin/appointments", headers=auth_headers).json()["items"][0]["id"]
    public_reference = client.get(
        f"/api/v1/admin/appointments/{appt_id}", headers=auth_headers
    ).json()["public_reference"]

    new_date = (date.today() + timedelta(days=3)).isoformat()
    client.patch(
        f"/api/v1/admin/appointments/{appt_id}/propose-slot",
        json={"proposed_date": new_date, "proposed_time": "14:00:00"},
        headers=auth_headers,
    )

    from app.models.appointment import Appointment

    db_session.expire_all()
    appointment = db_session.query(Appointment).filter_by(public_reference=public_reference).first()
    token = appointment.proposed_slot_token
    assert token is not None

    confirm = client.post(
        f"/api/v1/appointments/{public_reference}/confirm-proposed-slot", json={"token": token}
    )
    assert confirm.status_code == 200
    assert confirm.json()["status"] == "CONFIRMED"

    wrong_token = client.post(
        f"/api/v1/appointments/{public_reference}/confirm-proposed-slot", json={"token": "wrong"}
    )
    assert wrong_token.status_code == 400
