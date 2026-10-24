import enum


class PatientType(str, enum.Enum):
    NEW = "NEW"
    EXISTING = "EXISTING"


class AppointmentStatus(str, enum.Enum):
    PENDING = "PENDING"
    CONFIRMED = "CONFIRMED"
    ALTERNATE_PROPOSED = "ALTERNATE_PROPOSED"
    CANCELLED = "CANCELLED"
    COMPLETED = "COMPLETED"


class NotificationChannel(str, enum.Enum):
    WHATSAPP = "WHATSAPP"


class NotificationType(str, enum.Enum):
    CONFIRMATION = "CONFIRMATION"
    ALTERNATE_PROPOSAL = "ALTERNATE_PROPOSAL"


class NotificationStatus(str, enum.Enum):
    QUEUED = "QUEUED"
    SENT = "SENT"
    DELIVERED = "DELIVERED"
    FAILED = "FAILED"


# Status transitions an admin is allowed to request explicitly via the
# generic PATCH /admin/appointments/{id}/status endpoint. Accept and
# propose-slot have their own dedicated endpoints and are not reachable
# through this generic transition map.
ALLOWED_STATUS_TRANSITIONS: dict[AppointmentStatus, set[AppointmentStatus]] = {
    AppointmentStatus.PENDING: {AppointmentStatus.CANCELLED},
    AppointmentStatus.CONFIRMED: {AppointmentStatus.CANCELLED, AppointmentStatus.COMPLETED},
    AppointmentStatus.ALTERNATE_PROPOSED: {
        AppointmentStatus.CONFIRMED,
        AppointmentStatus.CANCELLED,
    },
    AppointmentStatus.CANCELLED: set(),
    AppointmentStatus.COMPLETED: set(),
}
