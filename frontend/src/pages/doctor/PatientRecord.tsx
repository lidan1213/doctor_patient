import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { useAuthStore } from '../../stores/authStore'
import { fetchPatientRecord } from '../../api/doctor'
import PatientRecordView from '../../components/doctor/PatientRecordView'
import type { PatientRecordData } from '../../types'

export default function PatientRecord() {
  const { patientId } = useParams<{ patientId: string }>()
  const [patient, setPatient] = useState<PatientRecordData | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const navigate = useNavigate()
  const logout = useAuthStore((s) => s.logout)
  const token = useAuthStore((s) => s.token)

  useEffect(() => {
    if (!token) { navigate('/login'); return }
    if (!patientId) return
    setLoading(true)
    fetchPatientRecord(Number(patientId))
      .then(setPatient)
      .catch((err) => setError('加载失败: ' + (err.message || '未知错误')))
      .finally(() => setLoading(false))
  }, [patientId, token])

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
        <div style={{ display: 'flex', gap: 24, alignItems: 'center' }}>
          <h2 style={{ margin: 0, fontSize: 18, color: '#52c41a' }}>MedAgent · 患者记录</h2>
          <button onClick={() => navigate('/doctor/search')} style={{ padding: '4px 12px', border: '1px solid #d9d9d9', borderRadius: 4, background: '#fff', cursor: 'pointer', fontSize: 13, color: '#52c41a' }}>
            返回检索
          </button>
          <button onClick={() => navigate('/doctor/search-history')} style={{ padding: '4px 12px', border: '1px solid #d9d9d9', borderRadius: 4, background: '#fff', cursor: 'pointer', fontSize: 13, color: '#666' }}>
            检索历史
          </button>
        </div>
        <button onClick={() => { logout(); navigate('/login') }} style={{ padding: '4px 12px', border: '1px solid #d9d9d9', borderRadius: 4, background: '#fff', cursor: 'pointer' }}>
          退出
        </button>
      </header>

      <div style={{ flex: 1, overflowY: 'auto', padding: '24px 16px' }}>
        {loading && <div style={{ textAlign: 'center', color: '#999', padding: 24 }}>加载中...</div>}
        {error && (
          <div style={{ padding: 16, background: '#fff2f0', borderRadius: 8, color: '#ff4d4f', fontSize: 14 }}>{error}</div>
        )}
        {patient && <PatientRecordView patient={patient} />}
      </div>
    </div>
  )
}
