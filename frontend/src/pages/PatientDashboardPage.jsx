import { useState, useEffect, useCallback } from 'react'
import { useParams, useNavigate, Link } from 'react-router-dom'
import { patientService, reportService } from '../services/medlens'
import MedicalTestCard from '../components/MedicalTestCard'
import { ProcessingBadge, ProvenanceTag } from '../components/Badges'
import {
  User, FileText, FlaskConical, Brain, Upload, RefreshCw,
  ChevronLeft, AlertTriangle, HelpCircle, Plus, Loader
} from 'lucide-react'

// ── Sub-components ─────────────────────────────────────────────────────────────

function InfoSection({ title, icon, items, color, provenance = 'user' }) {
  if (!items || (Array.isArray(items) && items.length === 0) || (typeof items === 'string' && !items.trim())) return null
  const list = Array.isArray(items) ? items : [items]
  return (
    <div>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 10 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: '0.85rem', fontWeight: 600 }}>
          <span>{icon}</span> {title}
        </div>
        <ProvenanceTag source={provenance} />
      </div>
      <div className="tag-list">
        {list.map((item, i) => (
          <span key={i} className="tag" style={{ borderColor: `${color}30`, color }}>
            {item}
          </span>
        ))}
      </div>
    </div>
  )
}

function AISummaryPanel({ patientId }) {
  const [summary, setSummary] = useState(null)
  const [loading, setLoading] = useState(false)
  const [generating, setGenerating] = useState(false)

  useEffect(() => {
    patientService.getSummary(patientId).then(setSummary).catch(() => {})
  }, [patientId])

  const generate = async () => {
    setGenerating(true)
    try {
      const s = await patientService.generateSummary(patientId)
      setSummary(s)
    } catch (e) {
      console.error(e)
    } finally {
      setGenerating(false)
    }
  }

  return (
    <div className="ai-summary-panel">
      <div className="ai-summary-header">
        <div className="ai-summary-icon">🧠</div>
        <div>
          <div className="ai-summary-title">AI Generated Summary</div>
          {summary && (
            <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>
              {new Date(summary.created_at).toLocaleString()} · {summary.model_name}
            </div>
          )}
        </div>
        <button
          className="btn btn-ghost btn-sm"
          onClick={generate}
          disabled={generating}
          style={{ marginLeft: 'auto' }}
        >
          {generating ? <Loader size={14} style={{ animation: 'spin 0.7s linear infinite' }} /> : <RefreshCw size={14} />}
          {generating ? 'Generating…' : summary ? 'Regenerate' : 'Generate'}
        </button>
      </div>

      {summary ? (
        <div className="ai-summary-text">{summary.summary_text}</div>
      ) : (
        <div className="empty-state" style={{ padding: '24px 0' }}>
          <div style={{ fontSize: '32px' }}>🧠</div>
          <p>Generate a patient-friendly summary of all available information.</p>
        </div>
      )}

      <div className="alert alert-warning" style={{ marginTop: 16 }}>
        <AlertTriangle size={14} />
        This AI-generated summary is for information purposes only. It does not constitute a diagnosis or medical advice. Always consult a qualified healthcare professional.
      </div>
    </div>
  )
}

function ClarificationsPanel({ patientId }) {
  const [questions, setQuestions] = useState(null)
  const [loading, setLoading] = useState(false)

  const fetch = async () => {
    setLoading(true)
    try {
      const q = await patientService.getClarifications(patientId)
      setQuestions(q)
    } catch (e) { console.error(e) }
    finally { setLoading(false) }
  }

  if (!questions) {
    return (
      <div>
        <button className="btn btn-secondary btn-sm" onClick={fetch} disabled={loading}>
          <HelpCircle size={14} />
          {loading ? 'Generating…' : 'Generate Clarification Questions'}
        </button>
      </div>
    )
  }

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
        <span style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
          {questions.length} questions generated
        </span>
        <button className="btn btn-ghost btn-sm" onClick={fetch} disabled={loading}>
          <RefreshCw size={12} /> Refresh
        </button>
      </div>
      <div className="clarification-list">
        {questions.map((q, i) => (
          <div key={i} className="clarification-item">
            <div className="clarification-num">{i + 1}</div>
            <div className="clarification-text">{q}</div>
          </div>
        ))}
      </div>
      <div style={{ marginTop: 10, fontSize: '0.75rem', color: 'var(--text-muted)' }}>
        These are intake clarification questions only — not medical advice.
      </div>
    </div>
  )
}

// ── Main Page ──────────────────────────────────────────────────────────────────

export default function PatientDashboardPage() {
  const { patientId } = useParams()
  const navigate = useNavigate()
  const [patient, setPatient] = useState(null)
  const [reports, setReports] = useState([])
  const [tests, setTests] = useState([])
  const [loading, setLoading] = useState(true)
  const [activeTab, setActiveTab] = useState('overview')
  const [refreshingReports, setRefreshingReports] = useState(false)

  const fetchAll = useCallback(async () => {
    try {
      const [p, r, t] = await Promise.all([
        patientService.getPatient(patientId),
        reportService.getReports(patientId),
        patientService.getTests(patientId),
      ])
      setPatient(p)
      setReports(r)
      setTests(t)
    } catch (e) { console.error(e) }
    finally { setLoading(false) }
  }, [patientId])

  useEffect(() => { fetchAll() }, [fetchAll])

  // Poll for processing reports
  useEffect(() => {
    const processingReports = reports.filter(r => ['pending', 'processing'].includes(r.processing_status))
    if (processingReports.length === 0) return
    const timer = setInterval(async () => {
      const r = await reportService.getReports(patientId)
      setReports(r)
      const stillProcessing = r.filter(r => ['pending', 'processing'].includes(r.processing_status))
      if (stillProcessing.length === 0) {
        clearInterval(timer)
        const t = await patientService.getTests(patientId)
        setTests(t)
      }
    }, 3000)
    return () => clearInterval(timer)
  }, [reports, patientId])

  if (loading) {
    return (
      <div className="page-content" style={{ display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
        <div className="spinner" style={{ width: 36, height: 36 }} />
      </div>
    )
  }

  if (!patient) {
    return (
      <div className="page-content">
        <div className="page-container" style={{ paddingTop: 60 }}>
          <div className="empty-state">
            <div className="empty-state-icon">🔍</div>
            <h3>Patient not found</h3>
            <Link to="/" className="btn btn-secondary">Back to Dashboard</Link>
          </div>
        </div>
      </div>
    )
  }

  const initials = patient.full_name?.split(' ').map(n => n[0]).join('').slice(0, 2).toUpperCase() || '?'
  const abnormalTests = tests.filter(t => t.status === 'low' || t.status === 'high')
  const pendingTests = tests.filter(t => t.verification_status === 'pending')
  const processingReports = reports.filter(r => ['pending', 'processing'].includes(r.processing_status))

  return (
    <div className="page-content">
      <div className="page-container" style={{ paddingTop: 40, paddingBottom: 60 }}>
        {/* Back link */}
        <button className="btn btn-ghost btn-sm" onClick={() => navigate('/')} style={{ marginBottom: 24 }}>
          <ChevronLeft size={14} /> Dashboard
        </button>

        {/* Patient Header */}
        <div className="patient-header" style={{ marginBottom: 28 }}>
          <div className="patient-avatar">{initials}</div>
          <div className="patient-info">
            <h1 className="patient-name">{patient.full_name}</h1>
            <div className="patient-meta">
              {patient.age && <span className="patient-meta-item">🗓 Age {patient.age}</span>}
              {patient.sex && <span className="patient-meta-item" style={{ textTransform: 'capitalize' }}>⚧ {patient.sex}</span>}
              {patient.blood_group && <span className="patient-meta-item" style={{ color: 'var(--accent-amber)' }}>🩸 {patient.blood_group}</span>}
              <span className="patient-meta-item">📋 {reports.length} report{reports.length !== 1 ? 's' : ''}</span>
              <span className="patient-meta-item">🧪 {tests.length} test{tests.length !== 1 ? 's' : ''}</span>
            </div>
          </div>
          <button className="btn btn-primary btn-sm" onClick={() => navigate(`/patients/${patientId}/reports/upload`)}>
            <Upload size={14} /> Add Report
          </button>
        </div>

        {/* Processing banner */}
        {processingReports.length > 0 && (
          <div className="alert alert-info" style={{ marginBottom: 20 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8, flex: 1 }}>
              <Loader size={14} style={{ animation: 'spin 0.7s linear infinite' }} />
              <span>Processing {processingReports.length} report(s) with AI extraction… Results will appear automatically.</span>
            </div>
          </div>
        )}

        {/* Abnormal alerts */}
        {abnormalTests.length > 0 && (
          <div className="alert alert-warning" style={{ marginBottom: 20 }}>
            <AlertTriangle size={16} />
            <div>
              <strong>{abnormalTests.length} value{abnormalTests.length !== 1 ? 's' : ''} outside reported reference range</strong>
              {' — '}{abnormalTests.map(t => t.test_name).join(', ')}
              <div style={{ fontSize: '0.75rem', marginTop: 4 }}>Review the Lab Results tab and consult a healthcare professional.</div>
            </div>
          </div>
        )}

        {/* Processing bar */}
        {processingReports.length > 0 && (
          <div className="processing-bar" style={{ marginBottom: 24 }}>
            <div className="processing-bar-fill" />
          </div>
        )}

        {/* Stats row */}
        <div className="grid-3" style={{ gap: 12, marginBottom: 28 }}>
          <div className="stat-card">
            <div className="stat-value" style={{ color: 'var(--accent-amber)', fontSize: '1.6rem' }}>{pendingTests.length}</div>
            <div className="stat-label">Pending Review</div>
          </div>
          <div className="stat-card">
            <div className="stat-value" style={{ color: 'var(--accent-red)', fontSize: '1.6rem' }}>{abnormalTests.length}</div>
            <div className="stat-label">Outside Range</div>
          </div>
          <div className="stat-card">
            <div className="stat-value" style={{ color: 'var(--accent-green)', fontSize: '1.6rem' }}>
              {tests.filter(t => t.verification_status !== 'pending').length}
            </div>
            <div className="stat-label">Verified</div>
          </div>
        </div>

        {/* Tabs */}
        <div className="tab-nav">
          {['overview', 'labs', 'reports', 'summary'].map(tab => (
            <button
              key={tab}
              className={`tab-btn ${activeTab === tab ? 'active' : ''}`}
              onClick={() => setActiveTab(tab)}
            >
              {{ overview: '📋 Overview', labs: '🧪 Lab Results', reports: '📄 Reports', summary: '🧠 AI Summary' }[tab]}
              {tab === 'labs' && tests.length > 0 && (
                <span style={{ marginLeft: 6, background: 'var(--bg-glass)', borderRadius: 10, padding: '1px 7px', fontSize: '0.72rem' }}>
                  {tests.length}
                </span>
              )}
            </button>
          ))}
        </div>

        {/* Tab Content */}
        {activeTab === 'overview' && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
            <div className="card-floating">
              <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
                <InfoSection title="Symptoms / Concerns" icon="🤒" items={patient.symptoms} color="var(--accent-amber)" />
                <InfoSection title="Existing Conditions" icon="🏥" items={patient.existing_conditions} color="var(--accent-blue)" />
                <InfoSection title="Known Allergies" icon="⚠️" items={patient.allergies} color="var(--accent-red)" />
                <InfoSection title="Current Medications" icon="💊" items={patient.medications} color="var(--accent-teal)" />
                <InfoSection title="Notes" icon="📝" items={patient.notes} color="var(--text-secondary)" />

                {!patient.symptoms?.length && !patient.existing_conditions?.length && (
                  <div className="empty-state" style={{ padding: '20px 0' }}>
                    <div className="empty-state-icon" style={{ fontSize: '32px' }}>📋</div>
                    <p>No clinical information on file.</p>
                  </div>
                )}
              </div>
            </div>

            <div className="card-floating">
              <div className="section-header" style={{ marginBottom: 16 }}>
                <div className="section-title"><HelpCircle size={16} style={{ color: 'var(--accent-purple)' }} /> Clarification Questions</div>
              </div>
              <ClarificationsPanel patientId={patientId} />
            </div>
          </div>
        )}

        {activeTab === 'labs' && (
          <div>
            {tests.length === 0 ? (
              <div className="card-floating">
                <div className="empty-state">
                  <div className="empty-state-icon">🧪</div>
                  <h3>No lab results yet</h3>
                  <p>Upload a medical report to extract and view structured lab results.</p>
                  <button className="btn btn-primary" onClick={() => navigate(`/patients/${patientId}/reports/upload`)}>
                    <Upload size={15} /> Upload Report
                  </button>
                </div>
              </div>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
                {pendingTests.length > 0 && (
                  <div className="alert alert-warning">
                    <AlertTriangle size={14} />
                    <span>{pendingTests.length} result{pendingTests.length !== 1 ? 's' : ''} awaiting your review — verify or correct each value.</span>
                  </div>
                )}
                {tests.map(t => (
                  <MedicalTestCard
                    key={t.id}
                    test={t}
                    onUpdate={(updated) => setTests(prev => prev.map(x => x.id === updated.id ? updated : x))}
                  />
                ))}
              </div>
            )}
          </div>
        )}

        {activeTab === 'reports' && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
            <div style={{ display: 'flex', justifyContent: 'flex-end' }}>
              <button className="btn btn-primary btn-sm" onClick={() => navigate(`/patients/${patientId}/reports/upload`)}>
                <Plus size={14} /> Upload Report
              </button>
            </div>

            {reports.length === 0 ? (
              <div className="card-floating">
                <div className="empty-state">
                  <div className="empty-state-icon">📄</div>
                  <h3>No reports uploaded</h3>
                </div>
              </div>
            ) : (
              reports.map(r => (
                <div key={r.id} className="card-floating" style={{ display: 'flex', gap: 16, alignItems: 'flex-start' }}>
                  <div style={{ width: 40, height: 40, background: 'rgba(99,179,237,0.1)', borderRadius: 10, display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>
                    <FileText size={18} color="var(--accent-blue)" />
                  </div>
                  <div style={{ flex: 1 }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 4 }}>
                      <span style={{ fontWeight: 600, fontSize: '0.9rem' }}>{r.file_name}</span>
                      <ProcessingBadge status={r.processing_status} />
                    </div>
                    <div style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>
                      {r.report_type} · {r.report_date || 'Date unknown'} · Added {new Date(r.created_at).toLocaleDateString()}
                    </div>
                    {r.processing_status === 'review' && (
                      <button
                        className="btn btn-sm btn-secondary"
                        style={{ marginTop: 8 }}
                        onClick={() => setActiveTab('labs')}
                      >
                        Review Extracted Results →
                      </button>
                    )}
                    {r.processing_status === 'failed' && (
                      <button
                        className="btn btn-sm btn-secondary"
                        style={{ marginTop: 8 }}
                        onClick={() => reportService.reprocessReport(r.id).then(fetchAll)}
                      >
                        <RefreshCw size={12} /> Retry Processing
                      </button>
                    )}
                  </div>
                </div>
              ))
            )}
          </div>
        )}

        {activeTab === 'summary' && (
          <AISummaryPanel patientId={patientId} />
        )}
      </div>
    </div>
  )
}
