import uuid
from datetime import date, datetime, time, timedelta

from sqlalchemy.orm import Session

from app.repositories.appointment_repository import AppointmentRepository
from app.repositories.doctor_availability_repository import DoctorAvailabilityRepository


def _expand_slots(start: time, end: time, duration_minutes: int, on_date: date) -> list[time]:
    slots = []
    current = datetime.combine(on_date, start)
    end_dt = datetime.combine(on_date, end)
    while current < end_dt:
        slots.append(current.time())
        current += timedelta(minutes=duration_minutes)
    return slots


def list_available_slots(db: Session, *, doctor_id: uuid.UUID, on_date: date) -> list[time]:
    """Slots are derived from the doctor's configured weekly availability
    (admin-managed via /admin/doctors/{id}/availability), minus already
    requested/booked times for that date and, for today, past times.
    A doctor with no configured availability for that weekday has no slots.
    """
    day_of_week = on_date.weekday()  # 0=Monday .. 6=Sunday
    windows = DoctorAvailabilityRepository(db).list_active_for_doctor_and_day(doctor_id, day_of_week)

    all_slots: set[time] = set()
    for window in windows:
        all_slots.update(_expand_slots(window.start_time, window.end_time, window.slot_duration_minutes, on_date))

    taken = set(AppointmentRepository(db).list_requested_times(doctor_id=doctor_id, on_date=on_date))
    is_today = on_date == date.today()
    now = datetime.now().time()

    return sorted(
        slot for slot in all_slots if slot not in taken and not (is_today and slot <= now)
    )
