import { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { useAuth } from '../hooks/useAuth'
import { Activity, Eye, EyeOff, Loader } from 'lucide-react'

export default function LoginPage() {
  const [mode, setMode] = useState('login') // 'login' | 'signup'
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [showPass, setShowPass] = useState(false)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')
  const { signIn, signUp } = useAuth()
  const navigate = useNavigate()

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    setSuccess('')
    setLoading(true)
    try {
      if (mode === 'signup') {
        const { error: err } = await signUp(email, password)
        if (err) throw err
        setSuccess('Account created! Check your email to confirm, then sign in.')
        setMode('login')
      } else {
        const { error: err } = await signIn(email, password)
        if (err) throw err
        navigate('/')
      }
    } catch (err) {
      setError(err.message || 'Authentication failed')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="auth-bg" role="main" aria-label="Authentication page">
      <div className="auth-card animate-in" role="form" aria-labelledby="auth-title">
        <div className="auth-logo">
          <div className="auth-logo-mark">
            <Activity size={22} color="#080c12" strokeWidth={2.5} />
          </div>
          <div>
            <div style={{ fontFamily: 'var(--font-display)', fontWeight: 700, fontSize: '1.3rem' }}>MedLens</div>
            <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Clinical Intelligence Platform</div>
          </div>
        </div>

        <h2 id="auth-title" style={{ marginBottom: 6 }}>
          {mode === 'login' ? 'Sign in to your account' : 'Create your account'}
        </h2>
        <p style={{ fontSize: '0.875rem', marginBottom: 28, color: 'var(--text-secondary)' }}>
          {mode === 'login'
            ? 'Access your patients and medical records securely.'
            : 'Start organizing your medical information with AI.'}
        </p>

        {error && (
          <div className="alert alert-error" role="alert" aria-live="assertive" style={{ marginBottom: 16 }}>
            <span aria-hidden="true">⚠</span> {error}
          </div>
        )}
        {success && (
          <div className="alert alert-success" role="status" aria-live="polite" style={{ marginBottom: 16 }}>
            <span aria-hidden="true">✓</span> {success}
          </div>
        )}

        <form className="auth-form" onSubmit={handleSubmit} aria-label={mode === 'login' ? 'Sign in form' : 'Sign up form'}>
          <div className="form-group">
            <label htmlFor="email">Email address</label>
            <input
              id="email"
              type="email"
              className="form-input"
              placeholder="you@example.com"
              value={email}
              onChange={e => setEmail(e.target.value)}
              required
              autoComplete="email"
            />
          </div>

          <div className="form-group">
            <label htmlFor="password">Password</label>
            <div style={{ position: 'relative' }}>
              <input
                id="password"
                type={showPass ? 'text' : 'password'}
                className="form-input"
                placeholder="••••••••"
                value={password}
                onChange={e => setPassword(e.target.value)}
                required
                minLength={6}
                autoComplete={mode === 'login' ? 'current-password' : 'new-password'}
                style={{ paddingRight: 44 }}
              />
              <button
                type="button"
                className="btn btn-ghost btn-icon"
                onClick={() => setShowPass(!showPass)}
                style={{ position: 'absolute', right: 8, top: '50%', transform: 'translateY(-50%)' }}
                aria-label={showPass ? 'Hide password' : 'Show password'}
              >
                {showPass ? <EyeOff size={16} aria-hidden="true" /> : <Eye size={16} aria-hidden="true" />}
              </button>
            </div>
            {mode === 'signup' && (
              <span className="form-hint">At least 6 characters</span>
            )}
          </div>

          <button
            type="submit"
            className="btn btn-primary btn-lg btn-full"
            disabled={loading}
          >
            {loading ? <Loader size={18} className="spinner" style={{ animation: 'spin 0.7s linear infinite' }} /> : null}
            {loading ? 'Please wait…' : mode === 'login' ? 'Sign In' : 'Create Account'}
          </button>
        </form>

        <div className="auth-divider" style={{ margin: '24px 0' }}>or</div>

        <button
          className="btn btn-secondary btn-full"
          onClick={() => { setMode(mode === 'login' ? 'signup' : 'login'); setError(''); setSuccess('') }}
        >
          {mode === 'login' ? "Don't have an account? Sign up" : 'Already have an account? Sign in'}
        </button>

        <p style={{ marginTop: 24, fontSize: '0.75rem', color: 'var(--text-muted)', textAlign: 'center' }}>
          MedLens does not diagnose or treat medical conditions.
          Always consult a qualified healthcare professional.
        </p>
      </div>
    </div>
  )
}
