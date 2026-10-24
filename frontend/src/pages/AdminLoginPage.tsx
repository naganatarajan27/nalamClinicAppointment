import { SiteHeader } from '../components/SiteHeader'
import { AdminLoginForm } from '../features/admin-auth/AdminLoginForm'

export function AdminLoginPage() {
  return (
    <>
      <SiteHeader subtitle="Clinic administrator sign in" />
      <main className="page">
        <AdminLoginForm />
      </main>
    </>
  )
}
