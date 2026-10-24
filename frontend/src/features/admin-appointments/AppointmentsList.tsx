import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Alert } from '../../components/Alert'
import { Button } from '../../components/Button'
import { StatusBadge } from '../../components/StatusBadge'
import * as adminApi from '../../api/adminApi'
import { ApiError } from '../../api/client'
import { formatDate, formatTime } from '../../utils/datetime'
import type { AppointmentAdminListItem, AppointmentStatus } from '../../types/api'

const STATUS_OPTIONS: { value: AppointmentStatus | ''; label: string }[] = [
  { value: '', label: 'All statuses' },
  { value: 'PENDING', label: 'Pending review' },
  { value: 'ALTERNATE_PROPOSED', label: 'Alternate proposed' },
  { value: 'CONFIRMED', label: 'Confirmed' },
  { value: 'CANCELLED', label: 'Cancelled' },
  { value: 'COMPLETED', label: 'Completed' },
]

const PAGE_SIZE = 20

export function AppointmentsList() {
  const navigate = useNavigate()
  const [status, setStatus] = useState<AppointmentStatus | ''>('')
  const [query, setQuery] = useState('')
  const [page, setPage] = useState(1)
  const [items, setItems] = useState<AppointmentAdminListItem[]>([])
  const [total, setTotal] = useState(0)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    let cancelled = false
    setLoading(true)
    setError(null)
    adminApi
      .listAppointments({ status, q: query, page, page_size: PAGE_SIZE })
      .then((response) => {
        if (cancelled) return
        setItems(response.items)
        setTotal(response.total)
      })
      .catch((err) => {
        if (cancelled) return
        setError(err instanceof ApiError ? err.message : 'Could not load appointments.')
      })
      .finally(() => {
        if (!cancelled) setLoading(false)
      })
    return () => {
      cancelled = true
    }
  }, [status, query, page])

  const totalPages = Math.max(1, Math.ceil(total / PAGE_SIZE))

  return (
    <div>
      <div className="toolbar">
        <div className="form-field">
          <label htmlFor="search">Search</label>
          <input
            id="search"
            type="search"
            placeholder="Reference or patient name"
            value={query}
            onChange={(e) => {
              setPage(1)
              setQuery(e.target.value)
            }}
          />
        </div>
        <div className="form-field">
          <label htmlFor="statusFilter">Status</label>
          <select
            id="statusFilter"
            value={status}
            onChange={(e) => {
              setPage(1)
              setStatus(e.target.value as AppointmentStatus | '')
            }}
          >
            {STATUS_OPTIONS.map((opt) => (
              <option key={opt.value} value={opt.value}>
                {opt.label}
              </option>
            ))}
          </select>
        </div>
      </div>

      {error && <Alert variant="error">{error}</Alert>}

      <div className="card">
        {loading ? (
          <p>
            <span className="spinner spinner--dark" aria-hidden="true" /> Loading appointments...
          </p>
        ) : items.length === 0 ? (
          <p className="empty-state">No appointment requests match these filters.</p>
        ) : (
          <table className="data-table">
            <thead>
              <tr>
                <th>Reference</th>
                <th>Patient</th>
                <th>Doctor</th>
                <th>Requested</th>
                <th>Status</th>
                <th>Notification</th>
              </tr>
            </thead>
            <tbody>
              {items.map((item) => (
                <tr
                  key={item.id}
                  className="clickable"
                  tabIndex={0}
                  role="button"
                  onClick={() => navigate(`/admin/appointments/${item.id}`)}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter') navigate(`/admin/appointments/${item.id}`)
                  }}
                >
                  <td>{item.public_reference}</td>
                  <td>
                    {item.patient_name}
                    <div className="hint">{item.patient_type === 'NEW' ? 'New patient' : 'Existing patient'}</div>
                  </td>
                  <td>{item.doctor?.display_name ?? '—'}</td>
                  <td>
                    {formatDate(item.requested_date)} at {formatTime(item.requested_time)}
                  </td>
                  <td>
                    <StatusBadge status={item.status} />
                  </td>
                  <td>{item.latest_notification_status ? <StatusBadge status={item.latest_notification_status} /> : '—'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {totalPages > 1 && (
        <div className="toolbar" style={{ justifyContent: 'center' }}>
          <Button variant="secondary" disabled={page <= 1} onClick={() => setPage((p) => p - 1)}>
            Previous
          </Button>
          <span>
            Page {page} of {totalPages}
          </span>
          <Button variant="secondary" disabled={page >= totalPages} onClick={() => setPage((p) => p + 1)}>
            Next
          </Button>
        </div>
      )}
    </div>
  )
}
