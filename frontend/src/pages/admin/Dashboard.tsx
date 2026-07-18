import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuthStore } from '../../stores/authStore'
import axios from 'axios'

interface UserInfo {
  id: number
  username: string
  role: string
  name: string
  created_at: string | null
}

interface Stats {
  total_users: number
  users_by_role: Record<string, number>
  total_conversations: number
  total_reports: number
}

interface KbResult {
  id: string
  title: string
  content_preview: string
  content_length: number
  type: string
}

type Tab = 'stats' | 'users' | 'knowledge'

export default function AdminDashboard() {
  const [tab, setTab] = useState<Tab>('stats')
  const [stats, setStats] = useState<Stats | null>(null)
  const [users, setUsers] = useState<UserInfo[]>([])
  const [kbQuery, setKbQuery] = useState('')
  const [kbResults, setKbResults] = useState<KbResult[]>([])
  const [kbColl, setKbColl] = useState('kb_professional')
  const [loading, setLoading] = useState(false)
  const navigate = useNavigate()
  const token = useAuthStore((s) => s.token)
  const user = useAuthStore((s) => s.user)
  const logout = useAuthStore((s) => s.logout)
  const headers = { Authorization: `Bearer ${token}` }

  useEffect(() => {
    if (!token) navigate('/login')
  }, [token])

  useEffect(() => {
    if (tab === 'stats') {
      setLoading(true)
      axios.get('/api/admin/stats', { headers }).then((r) => setStats(r.data)).catch(() => {}).finally(() => setLoading(false))
    } else if (tab === 'users') {
      setLoading(true)
      axios.get('/api/admin/users', { headers }).then((r) => setUsers(r.data.users)).catch(() => {}).finally(() => setLoading(false))
    }
  }, [tab])

  const searchKb = async () => {
    if (!kbQuery.trim()) return
    setLoading(true)
    try {
      const r = await axios.get('/api/admin/knowledge/search', { headers, params: { q: kbQuery, collection: kbColl } })
      setKbResults(r.data.results)
    } catch { }
    setLoading(false)
  }

  return (
    <div style={{ display: 'flex', height: '100vh', background: '#f0f2f5' }}>
      {/* Sidebar */}
      <div style={{ width: 200, background: '#001529', color: '#fff', padding: '16px 0' }}>
        <h3 style={{ padding: '0 16px', margin: '0 0 16px', color: '#fff' }}>MedAgent 管理</h3>
        {([
          ['stats', '📊 系统统计'],
          ['users', '👥 用户管理'],
          ['knowledge', '📚 知识库'],
        ] as [Tab, string][]).map(([key, label]) => (
          <div key={key} onClick={() => setTab(key)}
            style={{ padding: '10px 16px', cursor: 'pointer', background: tab === key ? '#1890ff' : 'transparent', marginBottom: 2 }}>
            {label}
          </div>
        ))}
        <div style={{ marginTop: 24, padding: '10px 16px' }}>
          <button onClick={() => navigate('/admin/chat')} style={{ padding: '6px 12px', border: '1px solid #fff', borderRadius: 4, background: 'transparent', color: '#fff', cursor: 'pointer', fontSize: 13 }}>返回对话</button>
        </div>
      </div>

      {/* Content */}
      <div style={{ flex: 1, padding: 24, overflowY: 'auto' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 20 }}>
          <h2 style={{ margin: 0, fontSize: 20 }}>{tab === 'stats' ? '系统统计' : tab === 'users' ? '用户管理' : '知识库检索'}</h2>
          <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
            <span style={{ color: '#666' }}>{user?.name}</span>
            <button onClick={() => { logout(); navigate('/login') }} style={{ padding: '4px 12px', border: '1px solid #d9d9d9', borderRadius: 4, background: '#fff', cursor: 'pointer' }}>退出</button>
          </div>
        </div>

        {/* Stats */}
        {tab === 'stats' && stats && (
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr 1fr', gap: 16 }}>
            {[
              ['总用户数', stats.total_users],
              ['对话记录', stats.total_conversations],
              ['上传报告', stats.total_reports],
            ].map(([label, value]) => (
              <div key={label as string} style={{ background: '#fff', padding: 20, borderRadius: 8, boxShadow: '0 1px 4px rgba(0,0,0,0.05)' }}>
                <div style={{ fontSize: 13, color: '#999', marginBottom: 4 }}>{label}</div>
                <div style={{ fontSize: 28, fontWeight: 600, color: '#333' }}>{value}</div>
              </div>
            ))}
            <div style={{ background: '#fff', padding: 20, borderRadius: 8, boxShadow: '0 1px 4px rgba(0,0,0,0.05)' }}>
              <div style={{ fontSize: 13, color: '#999', marginBottom: 8 }}>用户分布</div>
              {Object.entries(stats.users_by_role).map(([role, count]) => (
                <div key={role} style={{ fontSize: 14, color: '#333', marginBottom: 4 }}>{role}: {count}</div>
              ))}
            </div>
          </div>
        )}
        {tab === 'stats' && !stats && !loading && <div style={{ color: '#999' }}>暂无数据</div>}
        {tab === 'stats' && loading && <div style={{ color: '#999' }}>加载中...</div>}

        {/* Users */}
        {tab === 'users' && (
          <div style={{ background: '#fff', borderRadius: 8, overflow: 'hidden' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 14 }}>
              <thead>
                <tr style={{ background: '#fafafa', borderBottom: '1px solid #e8e8e8' }}>
                  <th style={{ padding: '10px 16px', textAlign: 'left' }}>ID</th>
                  <th style={{ padding: '10px 16px', textAlign: 'left' }}>用户名</th>
                  <th style={{ padding: '10px 16px', textAlign: 'left' }}>名称</th>
                  <th style={{ padding: '10px 16px', textAlign: 'left' }}>角色</th>
                  <th style={{ padding: '10px 16px', textAlign: 'left' }}>注册时间</th>
                </tr>
              </thead>
              <tbody>
                {users.map((u) => (
                  <tr key={u.id} style={{ borderBottom: '1px solid #f0f0f0' }}>
                    <td style={{ padding: '10px 16px', color: '#999' }}>{u.id}</td>
                    <td style={{ padding: '10px 16px' }}>{u.username}</td>
                    <td style={{ padding: '10px 16px' }}>{u.name}</td>
                    <td style={{ padding: '10px 16px' }}>
                      <span style={{ padding: '2px 8px', borderRadius: 4, fontSize: 12, background: u.role === 'doctor' ? '#e6f7ff' : u.role === 'admin' ? '#fff7e6' : '#f6ffed', color: u.role === 'doctor' ? '#1890ff' : u.role === 'admin' ? '#fa8c16' : '#52c41a' }}>
                        {u.role === 'patient' ? '患者' : u.role === 'doctor' ? '医生' : '管理员'}
                      </span>
                    </td>
                    <td style={{ padding: '10px 16px', color: '#999', fontSize: 13 }}>{u.created_at?.slice(0, 10) || '-'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {/* Knowledge */}
        {tab === 'knowledge' && (
          <div>
            <div style={{ display: 'flex', gap: 8, marginBottom: 16 }}>
              <select value={kbColl} onChange={(e) => setKbColl(e.target.value)} style={{ padding: '8px', border: '1px solid #d9d9d9', borderRadius: 4, background: '#fff' }}>
                <option value="kb_professional">专业版知识库</option>
                <option value="kb_patient">患者版知识库</option>
              </select>
              <input value={kbQuery} onChange={(e) => setKbQuery(e.target.value)} onKeyDown={(e) => e.key === 'Enter' && searchKb()}
                placeholder="搜索知识库..." style={{ flex: 1, padding: '8px 12px', border: '1px solid #d9d9d9', borderRadius: 4, fontSize: 14 }}
              />
              <button onClick={searchKb} disabled={loading || !kbQuery.trim()} style={{ padding: '8px 20px', background: '#1677ff', color: '#fff', border: 'none', borderRadius: 4, cursor: 'pointer' }}>搜索</button>
            </div>
            {kbResults.map((r) => (
              <div key={r.id} style={{ background: '#fff', padding: 12, borderRadius: 8, marginBottom: 8, border: '1px solid #e8e8e8' }}>
                <div style={{ fontWeight: 600, marginBottom: 4, fontSize: 14 }}>{r.title}</div>
                <div style={{ fontSize: 12, color: '#999', marginBottom: 4 }}>类型: {r.type} | 长度: {r.content_length} 字</div>
                <div style={{ fontSize: 13, color: '#555', lineHeight: 1.6 }}>{r.content_preview}...</div>
              </div>
            ))}
            {kbResults.length === 0 && !loading && <div style={{ color: '#999', textAlign: 'center', padding: 24 }}>输入关键词搜索知识库</div>}
          </div>
        )}
      </div>
    </div>
  )
}
