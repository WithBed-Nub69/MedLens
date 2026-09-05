export function StatusBadge({ status }) {
  const map = {
    low:     { cls: 'badge-low',     label: '↓ Low' },
    high:    { cls: 'badge-high',    label: '↑ High' },
    normal:  { cls: 'badge-normal',  label: '✓ Normal' },
    unknown: { cls: 'badge-unknown', label: '— Unknown' },
  }
  const { cls, label } = map[status?.toLowerCase()] || map.unknown
  return <span className={`badge ${cls}`}>{label}</span>
}

export function VerificationBadge({ status }) {
  const map = {
    verified:  { cls: 'badge-verified',  label: '✓ Verified' },
    pending:   { cls: 'badge-pending',   label: '⏳ Pending' },
    corrected: { cls: 'badge-corrected', label: '✎ Corrected' },
  }
  const { cls, label } = map[status?.toLowerCase()] || map.pending
  return <span className={`badge ${cls}`}>{label}</span>
}

export function ProcessingBadge({ status }) {
  const map = {
    pending:    { cls: 'badge-pending',    label: 'Pending' },
    processing: { cls: 'badge-processing', label: '⏳ Processing...' },
    review:     { cls: 'badge-review',     label: '👁 Review' },
    verified:   { cls: 'badge-verified',   label: '✓ Done' },
    failed:     { cls: 'badge-failed',     label: '✗ Failed' },
  }
  const { cls, label } = map[status?.toLowerCase()] || map.pending
  return <span className={`badge ${cls}`}>{label}</span>
}

export function ProvenanceTag({ source }) {
  const map = {
    'user':   { cls: 'provenance-user',   label: 'User Provided' },
    'report': { cls: 'provenance-report', label: 'Report Extracted' },
    'ai':     { cls: 'provenance-ai',     label: 'AI Generated' },
  }
  const { cls, label } = map[source?.toLowerCase()] || map.report
  return <span className={`provenance ${cls}`}>{label}</span>
}
