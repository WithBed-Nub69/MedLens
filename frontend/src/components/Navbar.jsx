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
    <nav className="navbar">
      <div className="page-container">
        <div className="navbar-inner">
          <Link to="/" className="navbar-logo">
            <div className="logo-icon">
              <Activity size={16} color="#080c12" strokeWidth={2.5} />
            </div>
            MedLens
          </Link>

          {user && (
            <div className="navbar-actions">
              <Link to="/patients/new" className="btn btn-primary btn-sm">
                <Plus size={14} />
                New Patient
              </Link>
              <span className="user-badge">
                {user.email?.split('@')[0] || 'User'}
              </span>
              <button className="btn btn-ghost btn-icon" onClick={handleSignOut} title="Sign out">
                <LogOut size={16} />
              </button>
            </div>
          )}
        </div>
      </div>
    </nav>
  )
}
