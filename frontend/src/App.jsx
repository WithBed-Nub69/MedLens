import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { AuthProvider } from './hooks/useAuth'
import AuthGuard from './components/AuthGuard'
import Navbar from './components/Navbar'
import LoginPage from './pages/LoginPage'
import DashboardPage from './pages/DashboardPage'
import PatientIntakePage from './pages/PatientIntakePage'
import PatientDashboardPage from './pages/PatientDashboardPage'
import ReportUploadPage from './pages/ReportUploadPage'

function AppShell({ children }) {
  return (
    <div className="app-layout">
      <Navbar />
      {children}
    </div>
  )
}

function ProtectedShell({ children }) {
  return (
    <AuthGuard>
      <AppShell>{children}</AppShell>
    </AuthGuard>
  )
}

export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <Routes>
          {/* Public */}
          <Route path="/login" element={<LoginPage />} />

          {/* Protected */}
          <Route path="/" element={
            <ProtectedShell><DashboardPage /></ProtectedShell>
          } />
          <Route path="/patients/new" element={
            <ProtectedShell><PatientIntakePage /></ProtectedShell>
          } />
          <Route path="/patients/:patientId" element={
            <ProtectedShell><PatientDashboardPage /></ProtectedShell>
          } />
          <Route path="/patients/:patientId/reports/upload" element={
            <ProtectedShell><ReportUploadPage /></ProtectedShell>
          } />

          {/* Fallback */}
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </AuthProvider>
    </BrowserRouter>
  )
}
