import { Fragment, useEffect, useState } from 'react'
import { Alert } from '../../components/Alert'
import { Button } from '../../components/Button'
import { FormField } from '../../components/FormField'
import * as adminApi from '../../api/adminApi'
import { ApiError } from '../../api/client'
import type { DoctorAdmin } from '../../types/api'
import { DoctorAvailabilityPanel } from './DoctorAvailabilityPanel'

export function DoctorsManager() {
  const [doctors, setDoctors] = useState<DoctorAdmin[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [expandedId, setExpandedId] = useState<string | null>(null)
  const [busy, setBusy] = useState(false)

  const [newName, setNewName] = useState('')
  const [newSpecialty, setNewSpecialty] = useState('')
  const [createError, setCreateError] = useState<string | null>(null)

  function load() {
    setLoading(true)
    setError(null)
    adminApi
      .listAllDoctors()
      .then(setDoctors)
      .catch((err) => setError(err instanceof ApiError ? err.message : 'Could not load doctors.'))
      .finally(() => setLoading(false))
  }

  useEffect(load, [])

  async function handleCreate() {
    if (busy) return
    if (!newName.trim()) {
      setCreateError('Please enter a doctor name.')
      return
    }
    setBusy(true)
    setCreateError(null)
    try {
      await adminApi.createDoctor({ display_name: newName.trim(), specialty: newSpecialty.trim() || undefined })
      setNewName('')
      setNewSpecialty('')
      load()
    } catch (err) {
      setCreateError(err instanceof ApiError ? err.message : 'Could not add that doctor.')
    } finally {
      setBusy(false)
    }
  }

  async function handleToggleActive(doctor: DoctorAdmin) {
    if (busy) return
    setBusy(true)
    setError(null)
    try {
      await adminApi.updateDoctor(doctor.id, { is_active: !doctor.is_active })
      load()
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Could not update that doctor.')
    } finally {
      setBusy(false)
    }
  }

  return (
    <div>
      <div className="card">
        <h3 style={{ marginTop: 0 }}>Add a doctor</h3>
        {createError && <Alert variant="error">{createError}</Alert>}
        <div className="form-row" style={{ alignItems: 'end' }}>
          <FormField label="Name" htmlFor="newDoctorName">
            <input
              id="newDoctorName"
              type="text"
              value={newName}
              onChange={(e) => setNewName(e.target.value)}
              disabled={busy}
            />
          </FormField>
          <FormField label="Specialty (optional)" htmlFor="newDoctorSpecialty">
            <input
              id="newDoctorSpecialty"
              type="text"
              value={newSpecialty}
              onChange={(e) => setNewSpecialty(e.target.value)}
              disabled={busy}
            />
          </FormField>
        </div>
        <Button onClick={handleCreate} loading={busy} disabled={busy}>
          Add doctor
        </Button>
      </div>

      <div className="card">
        <h3 style={{ marginTop: 0 }}>Doctors</h3>
        {error && <Alert variant="error">{error}</Alert>}

        {loading ? (
          <p>
            <span className="spinner spinner--dark" aria-hidden="true" /> Loading doctors...
          </p>
        ) : doctors.length === 0 ? (
          <p className="empty-state">No doctors yet. Add one above.</p>
        ) : (
          <table className="data-table">
            <thead>
              <tr>
                <th>Name</th>
                <th>Specialty</th>
                <th>Active</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {doctors.map((doctor) => (
                <Fragment key={doctor.id}>
                  <tr>
                    <td>{doctor.display_name}</td>
                    <td>{doctor.specialty ?? '—'}</td>
                    <td>{doctor.is_active ? 'Yes' : 'No'}</td>
                    <td style={{ display: 'flex', gap: '0.5rem' }}>
                      <Button
                        variant="secondary"
                        disabled={busy}
                        onClick={() => setExpandedId(expandedId === doctor.id ? null : doctor.id)}
                      >
                        {expandedId === doctor.id ? 'Hide availability' : 'Manage availability'}
                      </Button>
                      <Button variant="secondary" disabled={busy} onClick={() => handleToggleActive(doctor)}>
                        {doctor.is_active ? 'Deactivate' : 'Activate'}
                      </Button>
                    </td>
                  </tr>
                  {expandedId === doctor.id && (
                    <tr>
                      <td colSpan={4}>
                        <DoctorAvailabilityPanel doctorId={doctor.id} />
                      </td>
                    </tr>
                  )}
                </Fragment>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  )
}
