import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { patientService } from '../services/medlens'
import { User, ChevronRight, Plus, X } from 'lucide-react'

function TagInput({ label, value, onChange, placeholder }) {
  const [input, setInput] = useState('')

  const add = () => {
    const trimmed = input.trim()
    if (trimmed && !value.includes(trimmed)) {
      onChange([...value, trimmed])
    }
    setInput('')
  }

  const remove = (item) => onChange(value.filter(v => v !== item))

  return (
    <div className="form-group">
      <label>{label}</label>
      <div style={{ display: 'flex', gap: 8 }}>
        <input
          type="text"
          className="form-input"
          value={input}
          onChange={e => setInput(e.target.value)}
          placeholder={placeholder}
          onKeyDown={e => { if (e.key === 'Enter') { e.preventDefault(); add() } }}
        />
        <button type="button" className="btn btn-secondary btn-sm" onClick={add} style={{ flexShrink: 0 }}>
          <Plus size={14} />
        </button>
      </div>
      {value.length > 0 && (
        <div className="tag-list">
          {value.map((item, i) => (
            <span key={i} className="tag">
              {item}
              <button type="button" className="tag-remove" onClick={() => remove(item)}>
                <X size={12} />
              </button>
            </span>
          ))}
        </div>
      )}
    </div>
  )
}

const BLOOD_GROUPS = ['A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-']

export default function PatientIntakePage() {
  const navigate = useNavigate()
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const [form, setForm] = useState({
    full_name: '',
    age: '',
    sex: '',
    date_of_birth: '',
    blood_group: '',
    symptoms: [],
    existing_conditions: [],
    allergies: [],
    medications: [],
    notes: [],
  })

  const setField = (k, v) => setForm(f => ({ ...f, [k]: v }))

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      const payload = {
        ...form,
        age: form.age ? parseInt(form.age) : null,
        date_of_birth: form.date_of_birth || null,
        blood_group: form.blood_group || null,
        sex: form.sex || null,
      }
      const patient = await patientService.createPatient(payload)
      navigate(`/patients/${patient.id}`)
    } catch (err) {
      setError(err.userMessage || err.message || 'Failed to create patient')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="page-content">
      <div className="page-container" style={{ paddingTop: 48, paddingBottom: 60, maxWidth: 760 }}>
        {/* Breadcrumb */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 32, color: 'var(--text-muted)', fontSize: '0.8rem' }}>
          <span style={{ cursor: 'pointer', color: 'var(--accent-blue)' }} onClick={() => navigate('/')}>Dashboard</span>
          <ChevronRight size={12} />
          <span>New Patient</span>
        </div>

        <div style={{ marginBottom: 32 }}>
          <div className="section-label">Patient Intake</div>
          <h1>New Patient Record</h1>
          <p style={{ marginTop: 8 }}>
            Information entered here is labeled <strong style={{ color: 'var(--accent-green)' }}>User Provided</strong> — it will not be mixed with report-extracted data.
          </p>
        </div>

        {error && (
          <div className="alert alert-error" style={{ marginBottom: 24 }}>
            <span>⚠</span> {error}
          </div>
        )}

        <form onSubmit={handleSubmit}>
          {/* Identity */}
          <div className="card-floating" style={{ marginBottom: 20 }}>
            <div className="section-header" style={{ marginBottom: 20 }}>
              <div className="section-title">
                <div className="section-icon" style={{ background: 'rgba(79,209,197,0.1)', color: 'var(--accent-teal)' }}>
                  <User size={14} />
                </div>
                Identity
              </div>
              <span className="provenance provenance-user">User Provided</span>
            </div>

            <div className="form-grid">
              <div className="form-group" style={{ gridColumn: '1 / -1' }}>
                <label htmlFor="full_name">Full Name *</label>
                <input
                  id="full_name"
                  type="text"
                  className="form-input"
                  placeholder="Patient full name"
                  value={form.full_name}
                  onChange={e => setField('full_name', e.target.value)}
                  required
                />
              </div>

              <div className="form-group">
                <label htmlFor="age">Age</label>
                <input
                  id="age"
                  type="number"
                  className="form-input"
                  placeholder="e.g. 34"
                  min={0}
                  max={150}
                  value={form.age}
                  onChange={e => setField('age', e.target.value)}
                />
              </div>

              <div className="form-group">
                <label htmlFor="sex">Sex</label>
                <select
                  id="sex"
                  className="form-select"
                  value={form.sex}
                  onChange={e => setField('sex', e.target.value)}
                >
                  <option value="">Select…</option>
                  <option value="male">Male</option>
                  <option value="female">Female</option>
                  <option value="other">Other</option>
                  <option value="prefer_not_to_say">Prefer not to say</option>
                </select>
              </div>

              <div className="form-group">
                <label htmlFor="date_of_birth">Date of Birth</label>
                <input
                  id="date_of_birth"
                  type="date"
                  className="form-input"
                  value={form.date_of_birth}
                  onChange={e => setField('date_of_birth', e.target.value)}
                />
              </div>

              <div className="form-group">
                <label htmlFor="blood_group">Blood Group</label>
                <select
                  id="blood_group"
                  className="form-select"
                  value={form.blood_group}
                  onChange={e => setField('blood_group', e.target.value)}
                >
                  <option value="">Unknown</option>
                  {BLOOD_GROUPS.map(g => <option key={g} value={g}>{g}</option>)}
                </select>
              </div>
            </div>
          </div>

          {/* Clinical Information */}
          <div className="card-floating" style={{ marginBottom: 20 }}>
            <div className="section-header" style={{ marginBottom: 20 }}>
              <div className="section-title">
                <div className="section-icon" style={{ background: 'rgba(183,148,244,0.1)', color: 'var(--accent-purple)' }}>
                  🩺
                </div>
                Clinical Information
              </div>
              <span className="provenance provenance-user">User Provided</span>
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
              <TagInput
                label="Symptoms / Concerns"
                value={form.symptoms}
                onChange={v => setField('symptoms', v)}
                placeholder="Type a symptom, press Enter"
              />
              <TagInput
                label="Existing Medical Conditions"
                value={form.existing_conditions}
                onChange={v => setField('existing_conditions', v)}
                placeholder="Type a condition, press Enter"
              />
              <TagInput
                label="Known Allergies"
                value={form.allergies}
                onChange={v => setField('allergies', v)}
                placeholder="Type an allergy, press Enter"
              />
              <TagInput
                label="Current Medications"
                value={form.medications}
                onChange={v => setField('medications', v)}
                placeholder="Type a medication, press Enter"
              />
              <TagInput
                label="Additional Notes"
                value={form.notes}
                onChange={v => setField('notes', v)}
                placeholder="Any other relevant information"
              />
            </div>
          </div>

          <div style={{ display: 'flex', gap: 12 }}>
            <button type="button" className="btn btn-secondary" onClick={() => navigate('/')}>
              Cancel
            </button>
            <button type="submit" className="btn btn-primary btn-lg" style={{ flex: 1 }} disabled={loading}>
              {loading ? 'Creating…' : 'Create Patient & Continue →'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
