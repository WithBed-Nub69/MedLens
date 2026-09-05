import { useState, useRef } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { reportService } from '../services/medlens'
import { Upload, FileText, X, ChevronLeft, Loader } from 'lucide-react'

const REPORT_TYPES = [
  { value: 'lab', label: '🧪 Laboratory / Blood Test' },
  { value: 'radiology', label: '🔬 Radiology / Imaging' },
  { value: 'prescription', label: '💊 Prescription' },
  { value: 'discharge', label: '🏥 Discharge Summary' },
  { value: 'other', label: '📄 Other' },
]

const ACCEPTED = '.pdf,.jpg,.jpeg,.png,.webp,.bmp,.tiff'

export default function ReportUploadPage() {
  const { patientId } = useParams()
  const navigate = useNavigate()

  const [mode, setMode] = useState('file') // 'file' | 'text'
  const [file, setFile] = useState(null)
  const [text, setText] = useState('')
  const [reportType, setReportType] = useState('lab')
  const [reportDate, setReportDate] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [dragOver, setDragOver] = useState(false)
  const fileRef = useRef()

  const handleFile = (f) => {
    if (!f) return
    const allowed = ['application/pdf', 'image/jpeg', 'image/png', 'image/webp', 'image/bmp', 'image/tiff']
    if (!allowed.includes(f.type)) {
      setError('Unsupported file type. Please upload PDF, JPEG, PNG, WEBP, BMP, or TIFF.')
      return
    }
    if (f.size > 20 * 1024 * 1024) {
      setError('File too large. Maximum 20 MB.')
      return
    }
    setError('')
    setFile(f)
  }

  const handleDrop = (e) => {
    e.preventDefault()
    setDragOver(false)
    handleFile(e.dataTransfer.files[0])
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    if (mode === 'file' && !file) { setError('Please select a file.'); return }
    if (mode === 'text' && !text.trim()) { setError('Please paste report text.'); return }

    setLoading(true)
    try {
      if (mode === 'file') {
        await reportService.uploadReport(patientId, file, reportType, reportDate || null)
      } else {
        await reportService.uploadTextReport(patientId, text.trim(), reportType, reportDate || null)
      }
      navigate(`/patients/${patientId}`)
    } catch (err) {
      setError(err.userMessage || err.message || 'Upload failed')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="page-content">
      <div className="page-container" style={{ paddingTop: 40, paddingBottom: 60, maxWidth: 680 }}>
        <button className="btn btn-ghost btn-sm" onClick={() => navigate(`/patients/${patientId}`)} style={{ marginBottom: 24 }}>
          <ChevronLeft size={14} /> Patient Dashboard
        </button>

        <div style={{ marginBottom: 32 }}>
          <div className="section-label">Report Upload</div>
          <h1>Add Medical Report</h1>
          <p style={{ marginTop: 8 }}>Upload a PDF or image. AI will extract structured data for your review.</p>
        </div>

        <form onSubmit={handleSubmit}>
          {/* Mode switcher */}
          <div className="tab-nav" style={{ maxWidth: 320, marginBottom: 24 }}>
            <button type="button" className={`tab-btn ${mode === 'file' ? 'active' : ''}`} onClick={() => setMode('file')}>
              📎 Upload File
            </button>
            <button type="button" className={`tab-btn ${mode === 'text' ? 'active' : ''}`} onClick={() => setMode('text')}>
              📝 Paste Text
            </button>
          </div>

          <div className="card-floating" style={{ marginBottom: 20 }}>
            {mode === 'file' ? (
              <>
                {/* Drop zone */}
                <div
                  className={`upload-zone ${dragOver ? 'drag-over' : ''}`}
                  onClick={() => fileRef.current?.click()}
                  onDragOver={e => { e.preventDefault(); setDragOver(true) }}
                  onDragLeave={() => setDragOver(false)}
                  onDrop={handleDrop}
                >
                  {file ? (
                    <>
                      <div className="upload-zone-icon" style={{ background: 'rgba(79,209,197,0.1)' }}>
                        <FileText size={26} color="var(--accent-teal)" />
                      </div>
                      <div style={{ fontWeight: 600, color: 'var(--text-primary)' }}>{file.name}</div>
                      <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                        {(file.size / 1024).toFixed(0)} KB
                      </div>
                      <button
                        type="button"
                        className="btn btn-ghost btn-sm"
                        onClick={e => { e.stopPropagation(); setFile(null) }}
                      >
                        <X size={14} /> Remove
                      </button>
                    </>
                  ) : (
                    <>
                      <div className="upload-zone-icon">
                        <Upload size={26} />
                      </div>
                      <div style={{ fontWeight: 600, color: 'var(--text-primary)' }}>Drop file here or click to browse</div>
                      <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                        PDF, JPEG, PNG, WEBP — up to 20 MB
                      </div>
                    </>
                  )}
                </div>
                <input
                  ref={fileRef}
                  type="file"
                  accept={ACCEPTED}
                  style={{ display: 'none' }}
                  onChange={e => handleFile(e.target.files[0])}
                />
              </>
            ) : (
              <div className="form-group">
                <label>Paste report text *</label>
                <textarea
                  className="form-textarea"
                  rows={12}
                  value={text}
                  onChange={e => setText(e.target.value)}
                  placeholder="Paste the full text of your medical report here…"
                  style={{ minHeight: 220, fontFamily: 'monospace', fontSize: '0.85rem' }}
                />
                <span className="form-hint">
                  AI will extract structured values from your pasted text. The full text is stored as the source.
                </span>
              </div>
            )}
          </div>

          {/* Metadata */}
          <div className="card-floating" style={{ marginBottom: 20 }}>
            <div className="form-grid">
              <div className="form-group">
                <label htmlFor="report_type">Report Type</label>
                <select
                  id="report_type"
                  className="form-select"
                  value={reportType}
                  onChange={e => setReportType(e.target.value)}
                >
                  {REPORT_TYPES.map(t => <option key={t.value} value={t.value}>{t.label}</option>)}
                </select>
              </div>
              <div className="form-group">
                <label htmlFor="report_date">Report Date (optional)</label>
                <input
                  id="report_date"
                  type="date"
                  className="form-input"
                  value={reportDate}
                  onChange={e => setReportDate(e.target.value)}
                />
                <span className="form-hint">Will be overridden by date extracted from the document if found.</span>
              </div>
            </div>
          </div>

          {error && (
            <div className="alert alert-error" style={{ marginBottom: 16 }}>
              <span>⚠</span> {error}
            </div>
          )}

          <div className="alert alert-info" style={{ marginBottom: 20 }}>
            <span>ℹ</span>
            <div>
              <strong>What happens next?</strong> After upload, AI will extract structured data in the background.
              You'll be taken to the patient dashboard where results appear automatically.
              Every extracted value requires your review before being considered verified.
            </div>
          </div>

          <div style={{ display: 'flex', gap: 12 }}>
            <button type="button" className="btn btn-secondary" onClick={() => navigate(`/patients/${patientId}`)}>
              Cancel
            </button>
            <button type="submit" className="btn btn-primary btn-lg" style={{ flex: 1 }} disabled={loading}>
              {loading ? (
                <><Loader size={16} style={{ animation: 'spin 0.7s linear infinite' }} /> Processing…</>
              ) : (
                <><Upload size={16} /> Upload & Extract</>
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
