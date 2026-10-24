import uuid
from datetime import time

from pydantic import BaseModel, ConfigDict, Field, model_validator


class DoctorAvailabilityBase(BaseModel):
    day_of_week: int = Field(ge=0, le=6, description="0=Monday .. 6=Sunday")
    start_time: time
    end_time: time
    slot_duration_minutes: int = Field(default=30, ge=5, le=240)
    is_active: bool = True

    @model_validator(mode="after")
    def validate_time_range(self) -> "DoctorAvailabilityBase":
        if self.start_time >= self.end_time:
            raise ValueError("Start time must be before end time.")
        return self


class DoctorAvailabilityCreate(DoctorAvailabilityBase):
    pass


class DoctorAvailabilityUpdate(BaseModel):
    day_of_week: int | None = Field(default=None, ge=0, le=6)
    start_time: time | None = None
    end_time: time | None = None
    slot_duration_minutes: int | None = Field(default=None, ge=5, le=240)
    is_active: bool | None = None


class DoctorAvailabilityOut(DoctorAvailabilityBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    doctor_id: uuid.UUID
