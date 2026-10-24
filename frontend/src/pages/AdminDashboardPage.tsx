import { useNavigate } from 'react-router-dom'
import { Button } from '../components/Button'
import { SiteHeader } from '../components/SiteHeader'
import { AppointmentsList } from '../features/admin-appointments/AppointmentsList'
import { useAuth } from '../features/admin-auth/AuthContext'

export function AdminDashboardPage() {
  const { admin, logout } = useAuth()
  const navigate = useNavigate()

  async function handleLogout() {
    await logout()
    navigate('/admin/login', { replace: true })
  }

  return (
    <>
      <SiteHeader
        subtitle="Appointment requests"
        actions={
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
            <span className="hint">{admin?.email}</span>
            <Button variant="secondary" onClick={handleLogout}>
              Log out
            </Button>
          </div>
        }
      />
      <main className="page page--wide">
        <AppointmentsList />
      </main>
    </>
  )
}
