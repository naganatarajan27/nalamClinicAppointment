import re
import uuid
from datetime import date, datetime, time

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from app.models.enums import AppointmentStatus, PatientType
from app.schemas.doctor import DoctorPublic

E164_RE = re.compile(r"^\+[1-9]\d{6,14}$")


def _validate_e164(value: str) -> str:
    value = value.strip()
    if not E164_RE.match(value):
        raise ValueError(
            "Enter the number in international format starting with '+' and the country code, "
            "e.g. +91XXXXXXXXXX."
        )
    return value


class AppointmentCreate(BaseModel):
    patient_name: str = Field(min_length=1, max_length=255)
    patient_type: PatientType
    phone_number: str
    whatsapp_number: str
    email: EmailStr | None = None
    doctor_id: uuid.UUID
    requested_date: date
    requested_time: time
    symptoms: str = Field(min_length=1, max_length=1000)

    @field_validator("phone_number", "whatsapp_number")
    @classmethod
    def validate_phone(cls, value: str) -> str:
        return _validate_e164(value)

    @field_validator("requested_date")
    @classmethod
    def validate_not_past(cls, value: date) -> date:
        if value < date.today():
            raise ValueError("Preferred appointment date cannot be in the past.")
        return value


class AppointmentCreated(BaseModel):
    public_reference: str
    status: AppointmentStatus


class AppointmentPublicStatus(BaseModel):
    """Minimal, enumeration-safe public lookup response."""

    public_reference: str
    status: AppointmentStatus
    doctor: DoctorPublic | None
    confirmed_date: date | None
    confirmed_time: time | None
    proposed_date: date | None
    proposed_time: time | None


class AppointmentAdminListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    public_reference: str
    patient_name: str
    patient_type: PatientType
    phone_number: str
    whatsapp_number_masked: str
    doctor: DoctorPublic | None
    requested_date: date
    requested_time: time
    status: AppointmentStatus
    created_at: datetime
    latest_notification_status: str | None = None


class AppointmentAdminDetail(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    public_reference: str
    patient_name: str
    patient_type: PatientType
    phone_number: str
    whatsapp_number: str
    email: str | None
    doctor: DoctorPublic | None
    requested_date: date
    requested_time: time
    confirmed_doctor: DoctorPublic | None
    confirmed_date: date | None
    confirmed_time: time | None
    proposed_doctor: DoctorPublic | None
    proposed_date: date | None
    proposed_time: time | None
    symptoms: str
    status: AppointmentStatus
    admin_note: str | None
    created_at: datetime
    updated_at: datetime
    reviewed_by_admin_id: uuid.UUID | None
    reviewed_at: datetime | None


class AcceptAppointmentRequest(BaseModel):
    admin_note: str | None = Field(default=None, max_length=2000)


class ProposeSlotRequest(BaseModel):
    proposed_date: date
    proposed_time: time
    proposed_doctor_id: uuid.UUID | None = None
    admin_note: str | None = Field(default=None, max_length=2000)

    @field_validator("proposed_date")
    @classmethod
    def validate_not_past(cls, value: date) -> date:
        if value < date.today():
            raise ValueError("Proposed date cannot be in the past.")
        return value


class StatusUpdateRequest(BaseModel):
    status: AppointmentStatus


class ConfirmProposedSlotRequest(BaseModel):
    token: str
