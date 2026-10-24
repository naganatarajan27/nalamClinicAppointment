export type PatientType = 'NEW' | 'EXISTING'

export type AppointmentStatus =
  | 'PENDING'
  | 'CONFIRMED'
  | 'ALTERNATE_PROPOSED'
  | 'CANCELLED'
  | 'COMPLETED'

export type NotificationStatus = 'QUEUED' | 'SENT' | 'DELIVERED' | 'FAILED'
export type NotificationType = 'CONFIRMATION' | 'ALTERNATE_PROPOSAL'

export interface Doctor {
  id: string
  display_name: string
  specialty: string | null
}

export interface DoctorAdmin extends Doctor {
  is_active: boolean
}

export interface AppointmentCreatePayload {
  patient_name: string
  patient_type: PatientType
  phone_number: string
  whatsapp_number: string
  email?: string
  doctor_id: string
  requested_date: string
  requested_time: string
  symptoms: string
}

export interface AppointmentCreated {
  public_reference: string
  status: AppointmentStatus
}

export interface AppointmentPublicStatus {
  public_reference: string
  status: AppointmentStatus
  doctor: Doctor | null
  confirmed_date: string | null
  confirmed_time: string | null
  proposed_date: string | null
  proposed_time: string | null
}

export interface AppointmentAdminListItem {
  id: string
  public_reference: string
  patient_name: string
  patient_type: PatientType
  phone_number: string
  whatsapp_number_masked: string
  doctor: Doctor | null
  requested_date: string
  requested_time: string
  status: AppointmentStatus
  created_at: string
  latest_notification_status: NotificationStatus | null
}

export interface AppointmentAdminDetail {
  id: string
  public_reference: string
  patient_name: string
  patient_type: PatientType
  phone_number: string
  whatsapp_number: string
  email: string | null
  doctor: Doctor | null
  requested_date: string
  requested_time: string
  confirmed_doctor: Doctor | null
  confirmed_date: string | null
  confirmed_time: string | null
  proposed_doctor: Doctor | null
  proposed_date: string | null
  proposed_time: string | null
  symptoms: string
  status: AppointmentStatus
  admin_note: string | null
  created_at: string
  updated_at: string
  reviewed_by_admin_id: string | null
  reviewed_at: string | null
}

export interface AppointmentListResponse {
  items: AppointmentAdminListItem[]
  total: number
  page: number
  page_size: number
}

export interface NotificationAttempt {
  id: string
  channel: 'WHATSAPP' | 'EMAIL'
  notification_type: NotificationType
  status: NotificationStatus
  provider_message_id: string | null
  attempt_count: number
  last_error_summary: string | null
  created_at: string
  sent_at: string | null
}

export interface DoctorAvailability {
  id: string
  doctor_id: string
  day_of_week: number // 0=Monday .. 6=Sunday
  start_time: string
  end_time: string
  slot_duration_minutes: number
  is_active: boolean
}

export interface DoctorAvailabilityInput {
  day_of_week: number
  start_time: string
  end_time: string
  slot_duration_minutes: number
  is_active?: boolean
}

export interface AdminMe {
  id: string
  email: string
}

export interface ApiErrorBody {
  detail: string | { msg: string; loc: (string | number)[] }[]
}
