import type { SearchResult } from '../../types'

interface Props {
  results: SearchResult[]
  loading: boolean
  onResultClick?: (result: SearchResult) => void
}

export default function SearchPanel({ results, loading, onResultClick }: Props) {
  if (loading) {
    return <div style={{ padding: 24, textAlign: 'center', color: '#999' }}>检索中...</div>
  }

  if (results.length === 0) {
    return <div style={{ padding: 24, textAlign: 'center', color: '#999' }}>请输入检索关键词</div>
  }

  return (
    <div style={{ padding: '8px 0' }}>
      {results.map((r) => (
        <div
          key={r.id}
          onClick={() => onResultClick?.(r)}
          style={{
            padding: '12px 16px',
            borderBottom: '1px solid #f0f0f0',
            cursor: 'pointer',
            transition: 'background 0.2s',
          }}
          onMouseEnter={(e) => (e.currentTarget.style.background = '#fafafa')}
          onMouseLeave={(e) => (e.currentTarget.style.background = 'transparent')}
        >
          <h4 style={{ margin: '0 0 6px 0', fontSize: 14, color: '#1677ff' }}>{r.title}</h4>
          <p style={{ margin: '0 0 8px 0', fontSize: 13, color: '#666', lineHeight: 1.5 }}>
            {r.content.slice(0, 200)}{r.content.length > 200 ? '...' : ''}
          </p>
          <div style={{ fontSize: 11, color: '#999' }}>
            <span>相关度: {(r.score * 100).toFixed(0)}%</span>
            <span style={{ marginLeft: 12 }}>类型: {r.source_type}</span>
            {r.source.evidence_level && (
              <span style={{ marginLeft: 12 }}>证据等级: {r.source.evidence_level}</span>
            )}
          </div>
        </div>
      ))}
    </div>
  )
}
