import { useEffect, useState } from 'react'
import { Alert } from '../../components/Alert'
import { Button } from '../../components/Button'
import { FormField } from '../../components/FormField'
import * as adminApi from '../../api/adminApi'
import { ApiError } from '../../api/client'
import type { DoctorAvailability } from '../../types/api'

const DAY_LABELS = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']

export function DoctorAvailabilityPanel({ doctorId }: { doctorId: string }) {
  const [windows, setWindows] = useState<DoctorAvailability[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [busy, setBusy] = useState(false)

  const [dayOfWeek, setDayOfWeek] = useState('0')
  const [startTime, setStartTime] = useState('09:00')
  const [endTime, setEndTime] = useState('13:00')
  const [slotDuration, setSlotDuration] = useState('30')

  function load() {
    setLoading(true)
    setError(null)
    adminApi
      .listDoctorAvailability(doctorId)
      .then(setWindows)
      .catch((err) => setError(err instanceof ApiError ? err.message : 'Could not load availability.'))
      .finally(() => setLoading(false))
  }

  useEffect(load, [doctorId])

  async function handleAdd() {
    if (busy) return
    setBusy(true)
    setError(null)
    try {
      await adminApi.createDoctorAvailability(doctorId, {
        day_of_week: Number(dayOfWeek),
        start_time: `${startTime}:00`,
        end_time: `${endTime}:00`,
        slot_duration_minutes: Number(slotDuration),
      })
      load()
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Could not add that availability window.')
    } finally {
      setBusy(false)
    }
  }

  async function handleToggleActive(window: DoctorAvailability) {
    if (busy) return
    setBusy(true)
    setError(null)
    try {
      await adminApi.updateDoctorAvailability(doctorId, window.id, { is_active: !window.is_active })
      load()
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Could not update that availability window.')
    } finally {
      setBusy(false)
    }
  }

  async function handleDelete(window: DoctorAvailability) {
    if (busy) return
    if (!window.id) return
    setBusy(true)
    setError(null)
    try {
      await adminApi.deleteDoctorAvailability(doctorId, window.id)
      load()
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Could not remove that availability window.')
    } finally {
      setBusy(false)
    }
  }

  return (
    <div style={{ background: 'var(--color-surface)', padding: '1rem', borderRadius: 'var(--radius)' }}>
      {error && <Alert variant="error">{error}</Alert>}

      {loading ? (
        <p>
          <span className="spinner spinner--dark" aria-hidden="true" /> Loading availability...
        </p>
      ) : windows.length === 0 ? (
        <p className="empty-state">No weekly availability configured yet — patients will see no bookable times.</p>
      ) : (
        <table className="data-table">
          <thead>
            <tr>
              <th>Day</th>
              <th>Hours</th>
              <th>Slot length</th>
              <th>Active</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            {windows.map((w) => (
              <tr key={w.id}>
                <td>{DAY_LABELS[w.day_of_week]}</td>
                <td>
                  {w.start_time.slice(0, 5)} – {w.end_time.slice(0, 5)}
                </td>
                <td>{w.slot_duration_minutes} min</td>
                <td>{w.is_active ? 'Yes' : 'No'}</td>
                <td style={{ display: 'flex', gap: '0.5rem' }}>
                  <Button variant="secondary" disabled={busy} onClick={() => handleToggleActive(w)}>
                    {w.is_active ? 'Disable' : 'Enable'}
                  </Button>
                  <Button variant="danger" disabled={busy} onClick={() => handleDelete(w)}>
                    Remove
                  </Button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}

      <div className="form-row" style={{ marginTop: '1rem', alignItems: 'end' }}>
        <FormField label="Day" htmlFor={`day-${doctorId}`}>
          <select id={`day-${doctorId}`} value={dayOfWeek} onChange={(e) => setDayOfWeek(e.target.value)} disabled={busy}>
            {DAY_LABELS.map((label, idx) => (
              <option key={label} value={idx}>
                {label}
              </option>
            ))}
          </select>
        </FormField>
        <FormField label="Start time" htmlFor={`start-${doctorId}`}>
          <input
            id={`start-${doctorId}`}
            type="time"
            value={startTime}
            onChange={(e) => setStartTime(e.target.value)}
            disabled={busy}
          />
        </FormField>
      </div>
      <div className="form-row" style={{ alignItems: 'end' }}>
        <FormField label="End time" htmlFor={`end-${doctorId}`}>
          <input
            id={`end-${doctorId}`}
            type="time"
            value={endTime}
            onChange={(e) => setEndTime(e.target.value)}
            disabled={busy}
          />
        </FormField>
        <FormField label="Slot length (minutes)" htmlFor={`slot-${doctorId}`}>
          <input
            id={`slot-${doctorId}`}
            type="number"
            min={5}
            max={240}
            step={5}
            value={slotDuration}
            onChange={(e) => setSlotDuration(e.target.value)}
            disabled={busy}
          />
        </FormField>
      </div>
      <Button onClick={handleAdd} loading={busy} disabled={busy}>
        Add availability window
      </Button>
    </div>
  )
}
