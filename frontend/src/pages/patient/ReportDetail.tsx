import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { interpretReport } from '../../api/report'
import type { ReportInterpretation } from '../../types'

export default function ReportDetail() {
  const { reportId } = useParams<{ reportId: string }>()
  const [result, setResult] = useState<ReportInterpretation | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const navigate = useNavigate()

  useEffect(() => {
    if (!reportId) return
    setLoading(true)
    interpretReport(reportId)
      .then(setResult)
      .catch((err) => setError('加载报告失败: ' + (err.message || '未知错误')))
      .finally(() => setLoading(false))
  }, [reportId])

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100vh', background: '#f5f5f5' }}>
      <header
        style={{
          background: '#fff',
          padding: '12px 24px',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          borderBottom: '1px solid #e8e8e8',
        }}
      >
        <h2 style={{ margin: 0, fontSize: 18, color: '#1677ff' }}>MedAgent · 报告解读</h2>
        <button onClick={() => navigate('/patient/chat')} style={{ padding: '4px 12px', border: '1px solid #d9d9d9', borderRadius: 4, background: '#fff', cursor: 'pointer' }}>
          返回
        </button>
      </header>

      <div style={{ flex: 1, overflowY: 'auto', padding: '24px 16px' }}>
        {loading && <div style={{ textAlign: 'center', color: '#999', padding: 24 }}>加载中...</div>}
        {error && (
          <div style={{ padding: 16, background: '#fff2f0', borderRadius: 8, color: '#ff4d4f', fontSize: 14 }}>{error}</div>
        )}
        {result && (
          <div style={{ background: '#fff', borderRadius: 8, padding: 20, border: '1px solid #e8e8e8' }}>
            <div style={{ fontWeight: 600, fontSize: 16, color: '#1677ff', marginBottom: 12 }}>报告综合解读</div>
            <div style={{ fontSize: 14, lineHeight: 1.8, color: '#333', marginBottom: 20 }}>{result.summary}</div>

            {result.sections.map((section, i) => (
              <div key={i} style={{ marginBottom: 16, padding: '12px 16px', background: '#fafafa', borderRadius: 6 }}>
                <div style={{ fontWeight: 600, fontSize: 14, color: '#555', marginBottom: 6 }}>{section.title}</div>
                <div style={{ fontSize: 13, lineHeight: 1.6, color: '#666' }}>{section.content}</div>
              </div>
            ))}

            <div style={{ fontSize: 12, color: '#999', fontStyle: 'italic', marginTop: 16 }}>{result.disclaimer}</div>
          </div>
        )}
      </div>
    </div>
  )
}
