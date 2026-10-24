from datetime import date, time

from app.integrations.whatsapp.factory import get_whatsapp_adapter
from app.integrations.whatsapp.mock_adapter import MockWhatsAppAdapter
from app.models.enums import NotificationStatus


def test_factory_returns_mock_adapter_by_default():
    adapter = get_whatsapp_adapter()
    assert isinstance(adapter, MockWhatsAppAdapter)


def test_mock_adapter_never_claims_a_real_send(caplog):
    caplog.set_level("INFO")
    adapter = MockWhatsAppAdapter()
    result = adapter.send_confirmation(
        whatsapp_number="+919876543210",
        patient_name="Jane Doe",
        doctor_name="Dr. Asha Rao",
        appointment_date=date.today(),
        appointment_time=time(10, 30),
        reference_number="NAL-TEST1234",
    )
    assert result.status == NotificationStatus.SENT
    assert result.provider_message_id.startswith("mock-")
    assert any("MOCK" in record.message for record in caplog.records)


def test_mock_adapter_alternate_proposal(caplog):
    caplog.set_level("INFO")
    adapter = MockWhatsAppAdapter()
    result = adapter.send_alternate_proposal(
        whatsapp_number="+919876543210",
        patient_name="Jane Doe",
        doctor_name="Dr. Asha Rao",
        proposed_date=date.today(),
        proposed_time=time(14, 0),
        reference_number="NAL-TEST1234",
        next_step="call the clinic",
    )
    assert result.status == NotificationStatus.SENT
    assert any("MOCK" in record.message for record in caplog.records)
