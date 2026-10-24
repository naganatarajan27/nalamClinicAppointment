import { useCallback, useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { Alert } from '../../components/Alert'
import { Button } from '../../components/Button'
import { FormField } from '../../components/FormField'
import { StatusBadge } from '../../components/StatusBadge'
import * as adminApi from '../../api/adminApi'
import { ApiError } from '../../api/client'
import { formatDate, formatDateTime, formatTime } from '../../utils/datetime'
import { isPastDate, todayIsoDate } from '../../utils/validation'
import type { AppointmentAdminDetail, NotificationAttempt } from '../../types/api'

const CAN_ACCEPT = new Set(['PENDING', 'ALTERNATE_PROPOSED'])
const CAN_PROPOSE = new Set(['PENDING', 'ALTERNATE_PROPOSED'])
const CAN_CANCEL = new Set(['PENDING', 'ALTERNATE_PROPOSED', 'CONFIRMED'])

export function AppointmentDetail({ appointmentId }: { appointmentId: string }) {
  const [appointment, setAppointment] = useState<AppointmentAdminDetail | null>(null)
  const [notifications, setNotifications] = useState<NotificationAttempt[]>([])
  const [loading, setLoading] = useState(true)
  const [loadError, setLoadError] = useState<string | null>(null)
  const [actionError, setActionError] = useState<string | null>(null)
  const [actionMessage, setActionMessage] = useState<string | null>(null)
  const [busy, setBusy] = useState(false)

  const [adminNote, setAdminNote] = useState('')
  const [showProposeForm, setShowProposeForm] = useState(false)
  const [proposedDate, setProposedDate] = useState('')
  const [proposedTime, setProposedTime] = useState('')

  const load = useCallback(() => {
    setLoading(true)
    setLoadError(null)
    Promise.all([adminApi.getAppointment(appointmentId), adminApi.listNotifications(appointmentId)])
      .then(([detail, notifs]) => {
        setAppointment(detail)
        setAdminNote(detail.admin_note ?? '')
        setNotifications(notifs)
      })
      .catch((err) => {
        setLoadError(err instanceof ApiError ? err.message : 'Could not load this appointment.')
      })
      .finally(() => setLoading(false))
  }, [appointmentId])

  useEffect(() => {
    load()
  }, [load])

  async function runAction(action: () => Promise<unknown>, successMessage: string) {
    if (busy) return
    setBusy(true)
    setActionError(null)
    setActionMessage(null)
    try {
      await action()
      setActionMessage(successMessage)
      load()
    } catch (err) {
      setActionError(err instanceof ApiError ? err.message : 'That action could not be completed.')
    } finally {
      setBusy(false)
    }
  }

  if (loading) {
    return (
      <p>
        <span className="spinner spinner--dark" aria-hidden="true" /> Loading appointment...
      </p>
    )
  }

  if (loadError || !appointment) {
    return <Alert variant="error">{loadError ?? 'Appointment not found.'}</Alert>
  }

  return (
    <div>
      <p>
        <Link to="/admin/appointments">&larr; Back to appointments</Link>
      </p>

      {actionError && <Alert variant="error">{actionError}</Alert>}
      {actionMessage && <Alert variant="success">{actionMessage}</Alert>}

      <div className="card">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline' }}>
          <h2 style={{ margin: 0 }}>{appointment.public_reference}</h2>
          <StatusBadge status={appointment.status} />
        </div>

        <div className="form-row" style={{ marginTop: '1rem' }}>
          <div>
            <p>
              <strong>Patient:</strong> {appointment.patient_name} (
              {appointment.patient_type === 'NEW' ? 'New patient' : 'Existing patient'})
            </p>
            <p>
              <strong>Phone:</strong> {appointment.phone_number}
            </p>
            <p>
              <strong>WhatsApp:</strong> {appointment.whatsapp_number}
            </p>
          </div>
          <div>
            <p>
              <strong>Requested:</strong> {appointment.doctor?.display_name ?? 'Unknown doctor'} —{' '}
              {formatDate(appointment.requested_date)} at {formatTime(appointment.requested_time)}
            </p>
            {appointment.confirmed_date && (
              <p>
                <strong>Confirmed:</strong> {appointment.confirmed_doctor?.display_name} —{' '}
                {formatDate(appointment.confirmed_date)} at {formatTime(appointment.confirmed_time ?? '')}
              </p>
            )}
            {appointment.proposed_date && (
              <p>
                <strong>Proposed:</strong> {appointment.proposed_doctor?.display_name} —{' '}
                {formatDate(appointment.proposed_date)} at {formatTime(appointment.proposed_time ?? '')}
              </p>
            )}
          </div>
        </div>

        <p>
          <strong>Symptoms / reason for visit:</strong>
        </p>
        <p>{appointment.symptoms}</p>

        <FormField label="Internal note (not visible to patients)" htmlFor="adminNote">
          <textarea
            id="adminNote"
            rows={3}
            value={adminNote}
            onChange={(e) => setAdminNote(e.target.value)}
            disabled={busy}
          />
        </FormField>

        <div style={{ display: 'flex', gap: '0.75rem', flexWrap: 'wrap' }}>
          {CAN_ACCEPT.has(appointment.status) && (
            <Button
              onClick={() =>
                runAction(
                  () => adminApi.acceptAppointment(appointment.id, adminNote),
                  'Appointment confirmed and a WhatsApp confirmation was sent.',
                )
              }
              loading={busy}
            >
              Accept requested slot
            </Button>
          )}

          {CAN_PROPOSE.has(appointment.status) && (
            <Button variant="secondary" onClick={() => setShowProposeForm((v) => !v)} disabled={busy}>
              Suggest a new slot
            </Button>
          )}

          {appointment.status === 'CONFIRMED' && (
            <Button
              variant="secondary"
              onClick={() => runAction(() => adminApi.updateStatus(appointment.id, 'COMPLETED'), 'Marked as completed.')}
              disabled={busy}
            >
              Mark completed
            </Button>
          )}

          {CAN_CANCEL.has(appointment.status) && (
            <Button
              variant="danger"
              onClick={() => {
                if (!window.confirm('Cancel this appointment?')) return
                runAction(
                  () => adminApi.updateStatus(appointment.id, 'CANCELLED'),
                  'Appointment cancelled.',
                )
              }}
              disabled={busy}
            >
              Cancel
            </Button>
          )}
        </div>

        {showProposeForm && (
          <div className="card" style={{ marginTop: '1rem', background: 'var(--color-surface)' }}>
            <div className="form-row">
              <FormField label="Proposed date" htmlFor="proposedDate">
                <input
                  id="proposedDate"
                  type="date"
                  min={todayIsoDate()}
                  value={proposedDate}
                  onChange={(e) => setProposedDate(e.target.value)}
                  disabled={busy}
                />
              </FormField>
              <FormField label="Proposed time" htmlFor="proposedTime">
                <input
                  id="proposedTime"
                  type="time"
                  value={proposedTime}
                  onChange={(e) => setProposedTime(e.target.value)}
                  disabled={busy}
                />
              </FormField>
            </div>
            <Button
              onClick={() => {
                if (!proposedDate || !proposedTime) {
                  setActionError('Please choose both a proposed date and time.')
                  return
                }
                if (isPastDate(proposedDate)) {
                  setActionError('The proposed date cannot be in the past.')
                  return
                }
                runAction(
                  () =>
                    adminApi.proposeSlot(appointment.id, {
                      proposed_date: proposedDate,
                      proposed_time: proposedTime.length === 5 ? `${proposedTime}:00` : proposedTime,
                      admin_note: adminNote || undefined,
                    }),
                  'Alternate slot proposed and a WhatsApp message was sent to the patient.',
                )
                setShowProposeForm(false)
              }}
              loading={busy}
            >
              Send proposed slot
            </Button>
          </div>
        )}
      </div>

      <div className="card">
        <h3 style={{ marginTop: 0 }}>Notification history</h3>
        {notifications.length === 0 ? (
          <p className="empty-state">No notifications sent yet.</p>
        ) : (
          <table className="data-table">
            <thead>
              <tr>
                <th>Type</th>
                <th>Status</th>
                <th>Attempts</th>
                <th>Sent at</th>
                <th>Last error</th>
              </tr>
            </thead>
            <tbody>
              {notifications.map((n) => (
                <tr key={n.id}>
                  <td>{n.notification_type === 'CONFIRMATION' ? 'Confirmation' : 'Alternate proposal'}</td>
                  <td>
                    <StatusBadge status={n.status} />
                  </td>
                  <td>{n.attempt_count}</td>
                  <td>{n.sent_at ? formatDateTime(n.sent_at) : '—'}</td>
                  <td>{n.last_error_summary ?? '—'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
        {notifications.some((n) => n.status === 'FAILED') && (
          <Button
            variant="secondary"
            onClick={() => runAction(() => adminApi.retryNotification(appointment.id), 'Notification retried.')}
            loading={busy}
          >
            Retry failed notification
          </Button>
        )}
      </div>
    </div>
  )
}
