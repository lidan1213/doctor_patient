import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuthStore } from '../../stores/authStore'
import { fetchCarePlan } from '../../api/patient'
import type { CarePlanItemData } from '../../types'

const STATUS_MAP: Record<string, { color: string; label: string }> = {
  active: { color: '#52c41a', label: '进行中' },
  completed: { color: '#999', label: '已完成' },
  paused: { color: '#fa8c16', label: '暂停' },
}

export default function CarePlan() {
  const [plans, setPlans] = useState<CarePlanItemData[]>([])
  const [loading, setLoading] = useState(true)
  const navigate = useNavigate()
  const token = useAuthStore((s) => s.token)
  const logout = useAuthStore((s) => s.logout)

  useEffect(() => {
    if (!token) { navigate('/login'); return }
    setLoading(true)
    fetchCarePlan()
      .then((data) => setPlans(data.plans))
      .catch(console.error)
      .finally(() => setLoading(false))
  }, [token])

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
          <h2 style={{ margin: 0, fontSize: 18, color: '#1677ff' }}>MedAgent · 康复计划</h2>
          <button onClick={() => navigate('/patient/chat')} style={{ padding: '4px 12px', border: '1px solid #d9d9d9', borderRadius: 4, background: '#fff', cursor: 'pointer', fontSize: 13, color: '#1677ff' }}>
            返回对话
          </button>
          <button onClick={() => navigate('/patient/history')} style={{ padding: '4px 12px', border: '1px solid #d9d9d9', borderRadius: 4, background: '#fff', cursor: 'pointer', fontSize: 13, color: '#666' }}>
            对话历史
          </button>
        </div>
        <button onClick={() => { logout(); navigate('/login') }} style={{ padding: '4px 12px', border: '1px solid #d9d9d9', borderRadius: 4, background: '#fff', cursor: 'pointer' }}>
          退出
        </button>
      </header>

      <div style={{ flex: 1, overflowY: 'auto', padding: '24px 16px' }}>
        {loading && <div style={{ textAlign: 'center', color: '#999', padding: 24 }}>加载中...</div>}
        {!loading && plans.length === 0 && (
          <div style={{ textAlign: 'center', color: '#999', padding: 24 }}>暂无康复计划</div>
        )}
        {plans.map((plan) => {
          const st = STATUS_MAP[plan.status] || STATUS_MAP.active
          return (
            <div
              key={plan.id}
              style={{
                background: '#fff',
                padding: 16,
                borderRadius: 8,
                marginBottom: 12,
                border: '1px solid #e8e8e8',
              }}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
                <span style={{ fontWeight: 600, fontSize: 15, color: '#333' }}>{plan.title}</span>
                <span style={{
                  padding: '0 8px',
                  borderRadius: 4,
                  background: st.color + '20',
                  color: st.color,
                  fontSize: 12,
                  fontWeight: 600,
                }}>
                  {st.label}
                </span>
              </div>
              {plan.description && (
                <div style={{ fontSize: 13, color: '#666', marginBottom: 8, lineHeight: 1.6 }}>{plan.description}</div>
              )}
              {plan.medication_schedule && (
                <div style={{ fontSize: 13, color: '#333', marginBottom: 4, background: '#fafafa', padding: '8px 12px', borderRadius: 4 }}>
                  <span style={{ fontWeight: 600 }}>用药计划: </span>
                  {plan.medication_schedule}
                </div>
              )}
              {plan.follow_up_date && (
                <div style={{ fontSize: 12, color: '#1677ff' }}>复诊日期: {plan.follow_up_date}</div>
              )}
            </div>
          )
        })}
      </div>
    </div>
  )
}
