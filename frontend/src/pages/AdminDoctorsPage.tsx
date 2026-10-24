import { Link } from 'react-router-dom'
import { SiteHeader } from '../components/SiteHeader'
import { DoctorsManager } from '../features/admin-doctors/DoctorsManager'

export function AdminDoctorsPage() {
  return (
    <>
      <SiteHeader subtitle="Doctors and availability" />
      <main className="page page--wide">
        <p>
          <Link to="/admin/appointments">&larr; Back to appointments</Link>
        </p>
        <DoctorsManager />
      </main>
    </>
  )
}
