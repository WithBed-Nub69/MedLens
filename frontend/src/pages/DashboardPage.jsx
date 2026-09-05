import { useState, useEffect } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useAuth } from '../hooks/useAuth'
import { patientService } from '../services/medlens'
import { ProcessingBadge } from '../components/Badges'
import { Plus, User, FileText, ChevronRight, Activity, TrendingUp } from 'lucide-react'

function PatientCard({ patient }) {
  const navigate = useNavigate()
  const initials = patient.full_name
    ?.split(' ')
    .map(n => n[0])
    .join('')
    .slice(0, 2)
    .toUpperCase() || '?'

  return (
    <div
      className="card-floating"
      style={{ cursor: 'pointer' }}
      onClick={() => navigate(`/patients/${patient.id}`)}
    >
      <div style={{ display: 'flex', alignItems: 'flex-start', gap: 16, marginBottom: 16 }}>
        <div
          className="patient-avatar"
          style={{ width: 48, height: 48, fontSize: 18, borderRadius: 12 }}
        >
          {initials}
        </div>
        <div style={{ flex: 1 }}>
          <h3 style={{ fontSize: '1rem', marginBottom: 4 }}>{patient.full_name}</h3>
          <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap' }}>
            {patient.age && (
              <span style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
                Age {patient.age}
              </span>
            )}
            {patient.sex && (
              <span style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', textTransform: 'capitalize' }}>
                {patient.sex}
              </span>
            )}
            {patient.blood_group && (
              <span style={{ fontSize: '0.8rem', color: 'var(--accent-amber)' }}>
                {patient.blood_group}
              </span>
            )}
          </div>
        </div>
        <ChevronRight size={16} color="var(--text-muted)" />
      </div>

      {patient.symptoms?.length > 0 && (
        <div style={{ marginBottom: 12 }}>
          <div className="tag-list">
            {patient.symptoms.slice(0, 3).map((s, i) => (
              <span key={i} className="tag">{s}</span>
            ))}
            {patient.symptoms.length > 3 && (
              <span className="tag">+{patient.symptoms.length - 3} more</span>
            )}
          </div>
        </div>
      )}

      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', paddingTop: 12, borderTop: '1px solid var(--border)' }}>
        <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
          Added {new Date(patient.created_at).toLocaleDateString()}
        </span>
        <span style={{ fontSize: '0.75rem', color: 'var(--accent-blue)', display: 'flex', alignItems: 'center', gap: 4 }}>
          View Record <ChevronRight size={12} />
        </span>
      </div>
    </div>
  )
}

export default function DashboardPage() {
  const { user } = useAuth()
  const [patients, setPatients] = useState([])
  const [loading, setLoading] = useState(true)
  const navigate = useNavigate()

  useEffect(() => {
    patientService.getPatients()
      .then(setPatients)
      .catch(console.error)
      .finally(() => setLoading(false))
  }, [])

  const greeting = () => {
    const h = new Date().getHours()
    if (h < 12) return 'Good morning'
    if (h < 17) return 'Good afternoon'
    return 'Good evening'
  }

  return (
    <div className="page-content">
      <div className="page-container" style={{ paddingTop: 48, paddingBottom: 60 }}>
        {/* Hero */}
        <div className="dashboard-hero" style={{ padding: 0, marginBottom: 40 }}>
          <div style={{ marginBottom: 8 }}>
            <span style={{ fontSize: '0.8rem', color: 'var(--accent-teal)', fontWeight: 600, letterSpacing: '0.06em', textTransform: 'uppercase' }}>
              MedLens Dashboard
            </span>
          </div>
          <h1 style={{ marginBottom: 8 }}>
            {greeting()}, {user?.email?.split('@')[0] || 'Doctor'}
          </h1>
          <p style={{ marginBottom: 32, maxWidth: 480 }}>
            Organize, extract, and understand clinical information from medical reports — with full traceability and AI assistance.
          </p>

          <div className="grid-3" style={{ gridTemplateColumns: 'repeat(3, 1fr)', gap: 16, maxWidth: 480 }}>
            <div className="stat-card">
              <div className="stat-value" style={{ color: 'var(--accent-teal)' }}>{patients.length}</div>
              <div className="stat-label">Patients</div>
            </div>
            <div className="stat-card">
              <div className="stat-value" style={{ color: 'var(--accent-blue)' }}>
                {patients.reduce((sum, p) => sum + (p.symptoms?.length || 0), 0)}
              </div>
              <div className="stat-label">Symptoms</div>
            </div>
            <div className="stat-card">
              <div className="stat-value" style={{ color: 'var(--accent-purple)' }}>AI</div>
              <div className="stat-label">Powered</div>
            </div>
          </div>
        </div>

        {/* Patients Section */}
        <div className="section-header">
          <div className="section-title">
            <div className="section-icon" style={{ background: 'rgba(79,209,197,0.1)', color: 'var(--accent-teal)' }}>
              <User size={14} />
            </div>
            Patient Records
          </div>
          <button className="btn btn-primary btn-sm" onClick={() => navigate('/patients/new')}>
            <Plus size={14} />
            Add Patient
          </button>
        </div>

        {loading ? (
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))', gap: 16 }}>
            {[1, 2, 3].map(i => (
              <div key={i} className="card-floating skeleton" style={{ height: 160 }} />
            ))}
          </div>
        ) : patients.length === 0 ? (
          <div className="card-floating">
            <div className="empty-state">
              <div className="empty-state-icon">🩺</div>
              <h3>No patients yet</h3>
              <p>Create your first patient record to get started with AI-powered medical report analysis.</p>
              <button className="btn btn-primary" onClick={() => navigate('/patients/new')}>
                <Plus size={16} />
                Create First Patient
              </button>
            </div>
          </div>
        ) : (
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))', gap: 16 }}>
            {patients.map(p => <PatientCard key={p.id} patient={p} />)}
          </div>
        )}

        {/* About panel */}
        <div className="card-floating" style={{ marginTop: 40, background: 'linear-gradient(135deg, rgba(79,209,197,0.04), rgba(99,179,237,0.04))' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 12 }}>
            <Activity size={18} color="var(--accent-teal)" />
            <span style={{ fontWeight: 600, color: 'var(--text-primary)' }}>About MedLens</span>
          </div>
          <p style={{ fontSize: '0.875rem', lineHeight: 1.7 }}>
            MedLens extracts and organizes information from your medical reports into structured, traceable records.
            All extracted data shows its source (user-provided, report-extracted, or AI-generated).
            <strong style={{ color: 'var(--accent-amber)' }}> MedLens does not diagnose, prescribe, or replace professional medical care.</strong>
          </p>
        </div>
      </div>
    </div>
  )
}
