import uuid
from datetime import date, datetime, time, timedelta

from sqlalchemy.orm import Session

from app.repositories.appointment_repository import AppointmentRepository

# First-release default clinic hours. Not clinic-configurable yet; see
# CLAUDE_REQUIREMENTS_NALAM_CLINIC.md section 4, item 7 for the intended
# future direction (per-clinic configured slots).
CLINIC_OPEN_TIME = time(9, 0)
CLINIC_CLOSE_TIME = time(17, 0)
SLOT_DURATION_MINUTES = 30


def _all_slots() -> list[time]:
    slots = []
    current = datetime.combine(date.today(), CLINIC_OPEN_TIME)
    end = datetime.combine(date.today(), CLINIC_CLOSE_TIME)
    while current < end:
        slots.append(current.time())
        current += timedelta(minutes=SLOT_DURATION_MINUTES)
    return slots


def list_available_slots(db: Session, *, doctor_id: uuid.UUID, on_date: date) -> list[time]:
    taken = set(AppointmentRepository(db).list_requested_times(doctor_id=doctor_id, on_date=on_date))
    is_today = on_date == date.today()
    now = datetime.now().time()
    return [
        slot
        for slot in _all_slots()
        if slot not in taken and not (is_today and slot <= now)
    ]
