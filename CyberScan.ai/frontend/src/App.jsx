import { Routes, Route, Navigate } from 'react-router-dom'
import useAuthStore from './store/authStore'

// Pages
import Landing    from './pages/Landing'
import Login      from './pages/Login'
import Register   from './pages/Register'
import Dashboard  from './pages/Dashboard'
import ScanPage   from './pages/ScanPage'
import ScanResult from './pages/ScanResult'
import Profile    from './pages/Profile'
import Admin      from './pages/Admin'
import ScansHistory from './pages/ScansHistory'
import Pricing    from './pages/Pricing'
import SchedulePage from './pages/SchedulePage'
import AttackSurface from './pages/AttackSurface'

// Layout
import DashboardLayout from './components/dashboard/DashboardLayout'

function PrivateRoute({ children }) {
  const token = useAuthStore(s => s.token)
  return token ? children : <Navigate to="/login" replace />
}

function AdminRoute({ children }) {
  const user = useAuthStore(s => s.user)
  const token = useAuthStore(s => s.token)
  return token && user?.is_admin ? children : <Navigate to="/dashboard" replace />
}

function PublicRoute({ children }) {
  const token = useAuthStore(s => s.token)
  return !token ? children : <Navigate to="/dashboard" replace />
}

export default function App() {
  return (
    <Routes>
      {/* Public */}
      <Route path="/"         element={<Landing />} />
      <Route path="/pricing"  element={<Pricing />} />
      <Route path="/login"    element={<PublicRoute><Login /></PublicRoute>} />
      <Route path="/register" element={<PublicRoute><Register /></PublicRoute>} />

      {/* Protected */}
      <Route path="/dashboard" element={<PrivateRoute><DashboardLayout /></PrivateRoute>}>
        <Route index             element={<Dashboard />} />
        <Route path="scan"       element={<ScanPage />} />
        <Route path="scans"      element={<ScansHistory />} />
        <Route path="scans/:id"  element={<ScanResult />} />
        <Route path="schedule"        element={<SchedulePage />} />
        <Route path="attack-surface"  element={<AttackSurface />} />
        <Route path="profile"    element={<Profile />} />
        <Route path="admin"      element={<AdminRoute><Admin /></AdminRoute>} />
      </Route>

      {/* Fallback */}
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}
