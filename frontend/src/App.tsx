import { Navigate, Route, BrowserRouter, Routes } from 'react-router-dom'
import { AdminAppointmentDetailPage } from './pages/AdminAppointmentDetailPage'
import { AdminDashboardPage } from './pages/AdminDashboardPage'
import { AdminLoginPage } from './pages/AdminLoginPage'
import { BookingPage } from './pages/BookingPage'
import { ConfirmSlotPage } from './pages/ConfirmSlotPage'
import { AuthProvider } from './features/admin-auth/AuthContext'
import { RequireAuth } from './features/admin-auth/RequireAuth'

export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <Routes>
          <Route path="/" element={<BookingPage />} />
          <Route path="/confirm/:reference" element={<ConfirmSlotPage />} />
          <Route path="/admin/login" element={<AdminLoginPage />} />
          <Route
            path="/admin/appointments"
            element={
              <RequireAuth>
                <AdminDashboardPage />
              </RequireAuth>
            }
          />
          <Route
            path="/admin/appointments/:id"
            element={
              <RequireAuth>
                <AdminAppointmentDetailPage />
              </RequireAuth>
            }
          />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </AuthProvider>
    </BrowserRouter>
  )
}
