import { apiRequest } from './client'
import type {
  AdminMe,
  AppointmentAdminDetail,
  AppointmentListResponse,
  AppointmentStatus,
  NotificationAttempt,
} from '../types/api'

export function login(email: string, password: string): Promise<{ csrf_token: string }> {
  return apiRequest('/admin/auth/login', { method: 'POST', body: { email, password } })
}

export function logout(): Promise<void> {
  return apiRequest('/admin/auth/logout', { method: 'POST' })
}

export function me(): Promise<AdminMe> {
  return apiRequest('/admin/auth/me')
}

export interface AppointmentFilters {
  status?: AppointmentStatus | ''
  date_from?: string
  date_to?: string
  q?: string
  page?: number
  page_size?: number
}

export function listAppointments(filters: AppointmentFilters): Promise<AppointmentListResponse> {
  return apiRequest('/admin/appointments', {
    query: {
      status: filters.status || undefined,
      date_from: filters.date_from || undefined,
      date_to: filters.date_to || undefined,
      q: filters.q || undefined,
      page: filters.page,
      page_size: filters.page_size,
    },
  })
}

export function getAppointment(id: string): Promise<AppointmentAdminDetail> {
  return apiRequest(`/admin/appointments/${id}`)
}

export function acceptAppointment(id: string, adminNote?: string): Promise<AppointmentAdminDetail> {
  return apiRequest(`/admin/appointments/${id}/accept`, {
    method: 'PATCH',
    body: { admin_note: adminNote || undefined },
  })
}

export function proposeSlot(
  id: string,
  payload: { proposed_date: string; proposed_time: string; proposed_doctor_id?: string; admin_note?: string },
): Promise<AppointmentAdminDetail> {
  return apiRequest(`/admin/appointments/${id}/propose-slot`, { method: 'PATCH', body: payload })
}

export function updateStatus(id: string, status: AppointmentStatus): Promise<AppointmentAdminDetail> {
  return apiRequest(`/admin/appointments/${id}/status`, { method: 'PATCH', body: { status } })
}

export function retryNotification(id: string): Promise<NotificationAttempt> {
  return apiRequest(`/admin/appointments/${id}/notifications/retry`, { method: 'POST' })
}

export function listNotifications(id: string): Promise<NotificationAttempt[]> {
  return apiRequest(`/admin/appointments/${id}/notifications`)
}
