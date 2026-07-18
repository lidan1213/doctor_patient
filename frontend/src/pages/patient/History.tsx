import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuthStore } from '../../stores/authStore'
import { fetchChatHistory } from '../../api/chat'
import type { ChatHistoryItem } from '../../types'

export default function History() {
  const [items, setItems] = useState<ChatHistoryItem[]>([])
  const [loading, setLoading] = useState(true)
  const [page, setPage] = useState(1)
  const [total, setTotal] = useState(0)
  const navigate = useNavigate()
  const token = useAuthStore((s) => s.token)
  const logout = useAuthStore((s) => s.logout)

  const load = async (p: number) => {
    if (!token) return
    setLoading(true)
    try {
      const data = await fetchChatHistory(token, p)
      if (p === 1) {
        setItems(data.items)
      } else {
        setItems((prev) => [...prev, ...data.items])
      }
      setTotal(data.total)
    } catch (err) {
      console.error('Failed to load history', err)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    if (!token) navigate('/login')
    else load(1)
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
          <h2 style={{ margin: 0, fontSize: 18, color: '#1677ff' }}>MedAgent · 对话历史</h2>
          <button onClick={() => navigate('/patient/chat')} style={{ padding: '4px 12px', border: '1px solid #d9d9d9', borderRadius: 4, background: '#fff', cursor: 'pointer', fontSize: 13, color: '#1677ff' }}>
            返回对话
          </button>
          <button onClick={() => navigate('/patient/care-plan')} style={{ padding: '4px 12px', border: '1px solid #d9d9d9', borderRadius: 4, background: '#fff', cursor: 'pointer', fontSize: 13, color: '#666' }}>
            康复计划
          </button>
        </div>
        <button onClick={() => { logout(); navigate('/login') }} style={{ padding: '4px 12px', border: '1px solid #d9d9d9', borderRadius: 4, background: '#fff', cursor: 'pointer' }}>
          退出
        </button>
      </header>

      <div style={{ flex: 1, overflowY: 'auto', padding: '24px 16px' }}>
        {loading && items.length === 0 && (
          <div style={{ textAlign: 'center', color: '#999', padding: 24 }}>加载中...</div>
        )}
        {!loading && items.length === 0 && (
          <div style={{ textAlign: 'center', color: '#999', padding: 24 }}>暂无对话历史</div>
        )}
        {items.map((item) => (
          <div
            key={item.session_id}
            style={{
              background: '#fff',
              padding: '12px 16px',
              borderRadius: 8,
              marginBottom: 8,
              border: '1px solid #e8e8e8',
              cursor: 'pointer',
            }}
          >
            <div style={{ fontSize: 14, color: '#333', marginBottom: 4, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
              {item.first_message || '(无内容)'}
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 12, color: '#999' }}>
              <span>{item.message_count} 条消息</span>
              <span>{new Date(item.last_message_at).toLocaleString()}</span>
            </div>
          </div>
        ))}
        {items.length < total && (
          <button
            onClick={() => { const np = page + 1; setPage(np); load(np) }}
            disabled={loading}
            style={{
              width: '100%',
              padding: '8px',
              border: '1px solid #d9d9d9',
              borderRadius: 4,
              background: '#fff',
              cursor: loading ? 'not-allowed' : 'pointer',
              fontSize: 13,
              color: '#1677ff',
            }}
          >
            {loading ? '加载中...' : '加载更多'}
          </button>
        )}
      </div>
    </div>
  )
}
