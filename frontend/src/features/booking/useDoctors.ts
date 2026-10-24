import { useEffect, useState } from 'react'
import { listDoctors } from '../../api/publicApi'
import type { Doctor } from '../../types/api'

export function useDoctors() {
  const [doctors, setDoctors] = useState<Doctor[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    let cancelled = false
    setLoading(true)
    listDoctors()
      .then((data) => {
        if (!cancelled) setDoctors(data)
      })
      .catch(() => {
        if (!cancelled) setError('Could not load the list of doctors. Please refresh the page.')
      })
      .finally(() => {
        if (!cancelled) setLoading(false)
      })
    return () => {
      cancelled = true
    }
  }, [])

  return { doctors, loading, error }
}
