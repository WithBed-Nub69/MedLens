import { useState } from 'react'
import { StatusBadge, VerificationBadge, ProvenanceTag } from './Badges'
import { testService } from '../services/medlens'
import { CheckCircle, Edit2, X, Save, ChevronDown, ChevronUp } from 'lucide-react'

export default function MedicalTestCard({ test: initialTest, onUpdate }) {
  const [test, setTest] = useState(initialTest)
  const [editing, setEditing] = useState(false)
  const [loading, setLoading] = useState(false)
  const [editForm, setEditForm] = useState({
    value: test.value ?? '',
    unit: test.unit ?? '',
    reference_low: test.reference_low ?? '',
    reference_high: test.reference_high ?? '',
    correction_note: '',
  })
  const [showDetails, setShowDetails] = useState(false)

  const handleVerify = async () => {
    setLoading(true)
    try {
      const updated = await testService.verifyTest(test.id)
      const newTest = { ...test, ...updated }
      setTest(newTest)
      onUpdate?.(newTest)
    } catch (e) {
      console.error('Verify failed', e)
    } finally {
      setLoading(false)
    }
  }

  const handleCorrect = async () => {
    setLoading(true)
    try {
      const payload = {
        value: editForm.value !== '' ? parseFloat(editForm.value) : undefined,
        unit: editForm.unit || undefined,
        reference_low: editForm.reference_low !== '' ? parseFloat(editForm.reference_low) : undefined,
        reference_high: editForm.reference_high !== '' ? parseFloat(editForm.reference_high) : undefined,
        correction_note: editForm.correction_note || undefined,
      }
      const updated = await testService.correctTest(test.id, payload)
      const newTest = { ...test, ...updated }
      setTest(newTest)
      onUpdate?.(newTest)
      setEditing(false)
    } catch (e) {
      console.error('Correct failed', e)
    } finally {
      setLoading(false)
    }
  }

  const displayValue = test.value !== null && test.value !== undefined
    ? `${test.value}${test.unit ? ' ' + test.unit : ''}`
    : test.value_text || '—'

  const refRange = test.reference_text ||
    (test.reference_low !== null && test.reference_high !== null
      ? `${test.reference_low}–${test.reference_high}${test.unit ? ' ' + test.unit : ''}`
      : 'No reference range provided')

  return (
    <div className={`test-card status-${test.status} animate-in`}>
      {/* Header row */}
      <div className="test-card-header">
        <div>
          <div className="test-name">{test.test_name}</div>
          <div className="test-card-meta" style={{ marginTop: 6 }}>
            <StatusBadge status={test.status} />
            <VerificationBadge status={test.verification_status} />
            <ProvenanceTag source={test.source} />
          </div>
        </div>
        <div style={{ textAlign: 'right' }}>
          <div className="test-value-block">
            <span className="test-value">{test.value ?? test.value_text ?? '—'}</span>
            {test.unit && test.value !== null && <span className="test-unit">{test.unit}</span>}
          </div>
          <div className="test-reference" style={{ marginTop: 4 }}>{refRange}</div>
        </div>
      </div>

      {/* Observation */}
      {test.observation && (
        <div style={{ fontSize: '0.82rem', color: 'var(--text-muted)', padding: '8px 12px', background: 'var(--bg-glass)', borderRadius: 8 }}>
          <span style={{ color: 'var(--text-secondary)', fontWeight: 500 }}>Observation: </span>
          {test.observation}
        </div>
      )}

      {/* Expandable details */}
      {(test.extraction_confidence !== null || test.original_extracted_value || test.correction_note) && (
        <button
          className="btn btn-ghost btn-sm"
          onClick={() => setShowDetails(!showDetails)}
          style={{ alignSelf: 'flex-start', padding: '4px 8px', fontSize: '0.75rem' }}
        >
          {showDetails ? <ChevronUp size={12} /> : <ChevronDown size={12} />}
          {showDetails ? 'Less' : 'Details'}
        </button>
      )}

      {showDetails && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 6, fontSize: '0.78rem', color: 'var(--text-muted)' }}>
          {test.extraction_confidence !== null && (
            <span>Extraction confidence: {Math.round(test.extraction_confidence * 100)}%</span>
          )}
          {test.original_extracted_value && (
            <span>Original extracted: {test.original_extracted_value}</span>
          )}
          {test.correction_note && (
            <span style={{ color: 'var(--accent-purple)' }}>Correction note: {test.correction_note}</span>
          )}
          {test.verified_at && (
            <span>Verified at: {new Date(test.verified_at).toLocaleString()}</span>
          )}
        </div>
      )}

      {/* Edit form */}
      {editing && (
        <div className="inline-edit-form">
          <div style={{ fontSize: '0.8rem', color: 'var(--accent-amber)', marginBottom: 4 }}>
            ✎ Correcting — original extraction will be preserved for traceability
          </div>
          <div className="inline-edit-grid">
            <div className="form-group">
              <label>Value</label>
              <input
                type="number"
                step="any"
                className="form-input"
                value={editForm.value}
                onChange={e => setEditForm(f => ({ ...f, value: e.target.value }))}
              />
            </div>
            <div className="form-group">
              <label>Unit</label>
              <input
                type="text"
                className="form-input"
                value={editForm.unit}
                onChange={e => setEditForm(f => ({ ...f, unit: e.target.value }))}
              />
            </div>
            <div className="form-group">
              <label>Ref Low</label>
              <input
                type="number"
                step="any"
                className="form-input"
                value={editForm.reference_low}
                onChange={e => setEditForm(f => ({ ...f, reference_low: e.target.value }))}
              />
            </div>
            <div className="form-group">
              <label>Ref High</label>
              <input
                type="number"
                step="any"
                className="form-input"
                value={editForm.reference_high}
                onChange={e => setEditForm(f => ({ ...f, reference_high: e.target.value }))}
              />
            </div>
            <div className="form-group" style={{ gridColumn: '1/-1' }}>
              <label>Correction Note (optional)</label>
              <input
                type="text"
                className="form-input"
                placeholder="Why was this corrected?"
                value={editForm.correction_note}
                onChange={e => setEditForm(f => ({ ...f, correction_note: e.target.value }))}
              />
            </div>
          </div>
          <div style={{ display: 'flex', gap: 8 }}>
            <button className="btn btn-primary btn-sm" onClick={handleCorrect} disabled={loading}>
              <Save size={13} /> {loading ? 'Saving…' : 'Save Correction'}
            </button>
            <button className="btn btn-ghost btn-sm" onClick={() => setEditing(false)}>
              <X size={13} /> Cancel
            </button>
          </div>
        </div>
      )}

      {/* Actions */}
      {!editing && test.verification_status === 'pending' && (
        <div className="test-actions">
          <button
            className="btn btn-sm"
            style={{ background: 'rgba(104,211,145,0.1)', color: 'var(--accent-green)', border: '1px solid rgba(104,211,145,0.2)' }}
            onClick={handleVerify}
            disabled={loading}
          >
            <CheckCircle size={13} />
            {loading ? '…' : 'Verify'}
          </button>
          <button className="btn btn-secondary btn-sm" onClick={() => setEditing(true)}>
            <Edit2 size={13} /> Correct
          </button>
        </div>
      )}
    </div>
  )
}
