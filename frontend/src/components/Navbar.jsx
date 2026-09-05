import { Link, useNavigate } from 'react-router-dom'
import { useAuth } from '../hooks/useAuth'
import { Activity, Plus, LogOut, User } from 'lucide-react'

export default function Navbar() {
  const { user, signOut } = useAuth()
  const navigate = useNavigate()

  const handleSignOut = async () => {
    await signOut()
    navigate('/login')
  }

  return (
    <nav className="navbar" role="navigation" aria-label="Main navigation">
      <div className="page-container">
        <div className="navbar-inner">
          <Link to="/" className="navbar-logo" aria-label="MedLens - Go to dashboard">
            <div className="logo-icon" aria-hidden="true">
              <Activity size={16} color="#080c12" strokeWidth={2.5} />
            </div>
            MedLens
          </Link>

          {user && (
            <div className="navbar-actions" role="toolbar" aria-label="User actions">
              <Link to="/patients/new" className="btn btn-primary btn-sm" aria-label="Create new patient record">
                <Plus size={14} aria-hidden="true" />
                New Patient
              </Link>
              <span className="user-badge" role="status" aria-label={`Logged in as ${user.email?.split('@')[0] || 'User'}`}>
                {user.email?.split('@')[0] || 'User'}
              </span>
              <button className="btn btn-ghost btn-icon" onClick={handleSignOut} title="Sign out" aria-label="Sign out of your account">
                <LogOut size={16} aria-hidden="true" />
              </button>
            </div>
          )}
        </div>
      </div>
    </nav>
  )
}
