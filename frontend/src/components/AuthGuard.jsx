import { Navigate } from 'react-router-dom'
import { useAuth } from '../hooks/useAuth'

export default function AuthGuard({ children }) {
  const { user, loading } = useAuth()

  if (loading) {
    return (
      <div style={{ minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center' }} role="status" aria-label="Loading application">
        <div className="spinner" style={{ width: 32, height: 32 }} aria-hidden="true" />
        <span className="sr-only">Loading...</span>
      </div>
    )
  }

  if (!user) return <Navigate to="/login" replace />
  return children
}
