import { useParams } from 'react-router-dom'
import { SiteHeader } from '../components/SiteHeader'
import { AppointmentDetail } from '../features/admin-appointments/AppointmentDetail'

export function AdminAppointmentDetailPage() {
  const { id } = useParams<{ id: string }>()

  return (
    <>
      <SiteHeader subtitle="Appointment detail" />
      <main className="page page--wide">{id && <AppointmentDetail appointmentId={id} />}</main>
    </>
  )
}
