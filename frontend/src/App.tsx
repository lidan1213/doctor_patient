import { Routes, Route, Navigate } from 'react-router-dom'
import { useAuthStore } from './stores/authStore'
import Login from './pages/Login'
import PatientChat from './pages/patient/Chat'
import PatientHistory from './pages/patient/History'
import PatientCarePlan from './pages/patient/CarePlan'
import PatientReportDetail from './pages/patient/ReportDetail'
import DoctorSearch from './pages/doctor/Search'
import DoctorPatientRecord from './pages/doctor/PatientRecord'
import DoctorSearchHistory from './pages/doctor/SearchHistory'
import AdminDashboard from './pages/admin/Dashboard'

function ProtectedRoute({ children, role }: { children: React.ReactNode; role?: string }) {
  const { token, user } = useAuthStore()
  if (!token) return <Navigate to="/login" replace />
  if (role && user?.role !== role) return <Navigate to={`/${user?.role}`} replace />
  return <>{children}</>
}

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route
        path="/patient/*"
        element={
          <ProtectedRoute role="patient">
            <Routes>
              <Route path="/chat" element={<PatientChat />} />
              <Route path="/history" element={<PatientHistory />} />
              <Route path="/care-plan" element={<PatientCarePlan />} />
              <Route path="/report/:reportId" element={<PatientReportDetail />} />
              <Route path="/" element={<Navigate to="/patient/chat" replace />} />
              <Route path="*" element={<Navigate to="/patient/chat" replace />} />
            </Routes>
          </ProtectedRoute>
        }
      />
      <Route
        path="/doctor/*"
        element={
          <ProtectedRoute role="doctor">
            <Routes>
              <Route path="/search" element={<DoctorSearch />} />
              <Route path="/patient/:patientId" element={<DoctorPatientRecord />} />
              <Route path="/search-history" element={<DoctorSearchHistory />} />
              <Route path="/" element={<Navigate to="/doctor/search" replace />} />
              <Route path="*" element={<Navigate to="/doctor/search" replace />} />
            </Routes>
          </ProtectedRoute>
        }
      />
      <Route
        path="/admin/*"
        element={
          <ProtectedRoute role="admin">
            <Routes>
              <Route path="/dashboard" element={<AdminDashboard />} />
              <Route path="/chat" element={<PatientChat />} />
              <Route path="/" element={<Navigate to="/admin/dashboard" replace />} />
              <Route path="*" element={<Navigate to="/admin/dashboard" replace />} />
            </Routes>
          </ProtectedRoute>
        }
      />
      <Route path="*" element={<Navigate to="/login" replace />} />
    </Routes>
  )
}
