from datetime import date, timedelta


def _valid_payload(doctor_id: str) -> dict:
    tomorrow = date.today() + timedelta(days=1)
    return {
        "patient_name": "Jane Doe",
        "patient_type": "NEW",
        "phone_number": "+919876543210",
        "whatsapp_number": "+919876543211",
        "doctor_id": doctor_id,
        "requested_date": tomorrow.isoformat(),
        "requested_time": "10:30:00",
        "symptoms": "Persistent cough for a week.",
    }


def test_list_doctors_only_returns_active(client, doctor, inactive_doctor):
    response = client.get("/api/v1/doctors")
    assert response.status_code == 200
    names = [d["display_name"] for d in response.json()]
    assert doctor.display_name in names
    assert inactive_doctor.display_name not in names


def test_valid_booking_creates_pending_request(client, doctor):
    response = client.post("/api/v1/appointments", json=_valid_payload(str(doctor.id)))
    assert response.status_code == 201
    body = response.json()
    assert body["status"] == "PENDING"
    assert body["public_reference"].startswith("NAL-")


def test_booking_rejects_missing_required_fields(client, doctor):
    payload = _valid_payload(str(doctor.id))
    del payload["patient_name"]
    response = client.post("/api/v1/appointments", json=payload)
    assert response.status_code == 422


def test_booking_rejects_invalid_phone_format(client, doctor):
    payload = _valid_payload(str(doctor.id))
    payload["whatsapp_number"] = "9876543210"  # missing '+' country code
    response = client.post("/api/v1/appointments", json=payload)
    assert response.status_code == 422


def test_booking_rejects_past_date(client, doctor):
    payload = _valid_payload(str(doctor.id))
    payload["requested_date"] = (date.today() - timedelta(days=1)).isoformat()
    response = client.post("/api/v1/appointments", json=payload)
    assert response.status_code == 422


def test_booking_rejects_inactive_doctor(client, inactive_doctor):
    payload = _valid_payload(str(inactive_doctor.id))
    response = client.post("/api/v1/appointments", json=payload)
    assert response.status_code == 400


def test_public_lookup_does_not_expose_symptoms_or_contact_details(client, doctor):
    created = client.post("/api/v1/appointments", json=_valid_payload(str(doctor.id))).json()
    response = client.get(f"/api/v1/appointments/{created['public_reference']}")
    assert response.status_code == 200
    body = response.json()
    assert "symptoms" not in body
    assert "phone_number" not in body
    assert "whatsapp_number" not in body
    assert "admin_note" not in body
    assert body["status"] == "PENDING"


def test_public_lookup_unknown_reference_returns_404(client):
    response = client.get("/api/v1/appointments/NAL-DOESNOTEXIST")
    assert response.status_code == 404
