import { useEffect, useState } from 'react'
import { getAvailability } from '../../api/publicApi'

export function useAvailability(doctorId: string, date: string) {
  const [times, setTimes] = useState<string[]>([])
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    if (!doctorId || !date) {
      setTimes([])
      return
    }
    let cancelled = false
    setLoading(true)
    getAvailability(doctorId, date)
      .then((data) => {
        if (!cancelled) setTimes(data.available_times ?? [])
      })
      .catch(() => {
        if (!cancelled) setTimes([])
      })
      .finally(() => {
        if (!cancelled) setLoading(false)
      })
    return () => {
      cancelled = true
    }
  }, [doctorId, date])

  return { times, loading }
}
