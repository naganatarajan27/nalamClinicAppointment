import { SiteHeader } from '../components/SiteHeader'
import { BookingForm } from '../features/booking/BookingForm'

export function BookingPage() {
  return (
    <>
      <SiteHeader subtitle="Appointment request" />
      <main className="page">
        <p>
          Submit your preferred appointment time. The clinic will confirm it or suggest another
          time, and will reach out to you on WhatsApp.
        </p>
        <BookingForm />
        <p className="notice-box">
          This form is for appointment requests only and is <strong>not an emergency service</strong>.
          If you have a medical emergency, please call your local emergency number or go to the
          nearest emergency room immediately.
        </p>
      </main>
    </>
  )
}
