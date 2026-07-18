import type { CitationSource } from '../../types'

interface Props {
  source: CitationSource
}

const sourceColors: Record<string, string> = {
  guideline: '#1677ff',
  literature: '#52c41a',
  drug: '#fa8c16',
  education: '#722ed1',
}

export default function CitationCard({ source }: Props) {
  const color = sourceColors[source.type] || '#666'

  return (
    <div
      style={{
        border: `1px solid ${color}`,
        borderRadius: 6,
        padding: '8px 12px',
        marginBottom: 6,
        fontSize: 12,
        cursor: source.url ? 'pointer' : 'default',
        color: '#333',
      }}
      onClick={() => source.url && window.open(source.url, '_blank')}
    >
      <span style={{ background: color, color: '#fff', padding: '1px 6px', borderRadius: 3, marginRight: 8, fontSize: 11 }}>
        {source.type === 'guideline' ? '指南' : source.type === 'literature' ? '文献' : source.type === 'drug' ? '药品' : '科普'}
      </span>
      <strong>{source.title}</strong>
      {source.evidence_level && (
        <span style={{ marginLeft: 8, color: '#999' }}>证据等级: {source.evidence_level}</span>
      )}
    </div>
  )
}
