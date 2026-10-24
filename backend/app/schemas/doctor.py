import uuid

from pydantic import BaseModel, ConfigDict


class DoctorPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    display_name: str
    specialty: str | None


class DoctorAdmin(DoctorPublic):
    is_active: bool


class DoctorCreate(BaseModel):
    display_name: str
    specialty: str | None = None
    is_active: bool = True


class DoctorUpdate(BaseModel):
    display_name: str | None = None
    specialty: str | None = None
    is_active: bool | None = None
