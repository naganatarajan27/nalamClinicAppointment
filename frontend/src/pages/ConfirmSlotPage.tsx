import { useEffect, useState } from 'react'
import { useParams, useSearchParams } from 'react-router-dom'
import { Alert } from '../components/Alert'
import { Button } from '../components/Button'
import { SiteHeader } from '../components/SiteHeader'
import { confirmProposedSlot, getAppointmentStatus } from '../api/publicApi'
import { ApiError } from '../api/client'
import { formatDate, formatTime } from '../utils/datetime'
import type { AppointmentPublicStatus } from '../types/api'

export function ConfirmSlotPage() {
  const { reference } = useParams<{ reference: string }>()
  const [searchParams] = useSearchParams()
  const token = searchParams.get('token') ?? ''

  const [appointment, setAppointment] = useState<AppointmentPublicStatus | null>(null)
  const [loading, setLoading] = useState(true)
  const [loadError, setLoadError] = useState<string | null>(null)
  const [confirming, setConfirming] = useState(false)
  const [confirmError, setConfirmError] = useState<string | null>(null)

  useEffect(() => {
    if (!reference) return
    setLoading(true)
    getAppointmentStatus(reference)
      .then(setAppointment)
      .catch((err) => setLoadError(err instanceof ApiError ? err.message : 'Could not load this appointment.'))
      .finally(() => setLoading(false))
  }, [reference])

  async function handleConfirm() {
    if (!reference || confirming) return
    setConfirming(true)
    setConfirmError(null)
    try {
      const updated = await confirmProposedSlot(reference, token)
      setAppointment(updated)
    } catch (err) {
      setConfirmError(
        err instanceof ApiError
          ? err.message
          : 'We could not confirm this slot. Please call the clinic instead.',
      )
    } finally {
      setConfirming(false)
    }
  }

  return (
    <>
      <SiteHeader subtitle="Confirm your proposed appointment slot" />
      <main className="page">
        {loading && (
          <p>
            <span className="spinner spinner--dark" aria-hidden="true" /> Loading...
          </p>
        )}

        {!loading && loadError && <Alert variant="error">{loadError}</Alert>}

        {!loading && !loadError && appointment && (
          <div className="card">
            <p>
              Reference: <strong>{appointment.public_reference}</strong>
            </p>

            {appointment.status === 'ALTERNATE_PROPOSED' && appointment.proposed_date && appointment.proposed_time && (
              <>
                <p>
                  The clinic has proposed <strong>{formatDate(appointment.proposed_date)}</strong> at{' '}
                  <strong>{formatTime(appointment.proposed_time)}</strong>
                  {appointment.doctor ? ` with ${appointment.doctor.display_name}` : ''}.
                </p>
                {confirmError && <Alert variant="error">{confirmError}</Alert>}
                {!token ? (
                  <Alert variant="error">
                    This link is missing its confirmation token. Please use the link from your
                    WhatsApp message, or call the clinic to confirm.
                  </Alert>
                ) : (
                  <Button onClick={handleConfirm} loading={confirming} disabled={confirming}>
                    Confirm this slot
                  </Button>
                )}
              </>
            )}

            {appointment.status === 'CONFIRMED' && (
              <Alert variant="success">
                Your appointment is confirmed
                {appointment.confirmed_date && appointment.confirmed_time
                  ? ` for ${formatDate(appointment.confirmed_date)} at ${formatTime(appointment.confirmed_time)}`
                  : ''}
                {appointment.doctor ? ` with ${appointment.doctor.display_name}` : ''}.
              </Alert>
            )}

            {appointment.status !== 'ALTERNATE_PROPOSED' && appointment.status !== 'CONFIRMED' && (
              <Alert variant="info">
                This appointment's status is {appointment.status.toLowerCase()}. Please contact the
                clinic if you have questions.
              </Alert>
            )}
          </div>
        )}
      </main>
    </>
  )
}
