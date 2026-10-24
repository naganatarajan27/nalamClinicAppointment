import type { ReactNode } from 'react'
import { Navigate } from 'react-router-dom'
import { useAuth } from './AuthContext'

export function RequireAuth({ children }: { children: ReactNode }) {
  const { admin, loading } = useAuth()

  if (loading) {
    return (
      <div className="page">
        <span className="spinner spinner--dark" aria-hidden="true" /> Loading...
      </div>
    )
  }

  if (!admin) {
    return <Navigate to="/admin/login" replace />
  }

  return <>{children}</>
}
