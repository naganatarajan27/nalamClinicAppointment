import { apiRequest } from './client'
import type {
  AppointmentCreatePayload,
  AppointmentCreated,
  AppointmentPublicStatus,
  Doctor,
} from '../types/api'

export function listDoctors(): Promise<Doctor[]> {
  return apiRequest<Doctor[]>('/doctors')
}

export function getAvailability(doctorId: string, date: string): Promise<{ available_times: string[] }> {
  return apiRequest('/availability', { query: { doctor_id: doctorId, date } })
}

export function createAppointment(payload: AppointmentCreatePayload): Promise<AppointmentCreated> {
  return apiRequest<AppointmentCreated>('/appointments', { method: 'POST', body: payload })
}

export function getAppointmentStatus(publicReference: string): Promise<AppointmentPublicStatus> {
  return apiRequest(`/appointments/${encodeURIComponent(publicReference)}`)
}

export function confirmProposedSlot(
  publicReference: string,
  token: string,
): Promise<AppointmentPublicStatus> {
  return apiRequest(`/appointments/${encodeURIComponent(publicReference)}/confirm-proposed-slot`, {
    method: 'POST',
    body: { token },
  })
}
