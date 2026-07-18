import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuthStore } from '../stores/authStore'
import axios from 'axios'

export default function Login() {
  const [mode, setMode] = useState<'login' | 'register'>('login')
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [name, setName] = useState('')
  const [role, setRole] = useState<'patient' | 'doctor'>('patient')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const setAuth = useAuthStore((s) => s.setAuth)
  const navigate = useNavigate()

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      if (mode === 'register') {
        await axios.post('/api/auth/register', { username, password, name, role })
        setMode('login')
        setError('注册成功，请登录')
        return
      }
      const res = await axios.post('/api/auth/login', { username, password })
      setAuth(res.data.token, res.data.user)
      navigate(`/${res.data.user.role}`)
    } catch (err: any) {
      if (mode === 'register') {
        const msg = err.response?.data?.detail || '注册失败'
        setError(typeof msg === 'string' ? msg : JSON.stringify(msg))
      } else {
        setError(err.response?.data?.detail || '用户名或密码错误')
      }
    } finally {
      setLoading(false)
    }
  }

  return (
    <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100%', background: '#f0f2f5' }}>
      <form onSubmit={handleSubmit} style={{ background: '#fff', padding: 40, borderRadius: 8, width: 360, boxShadow: '0 2px 8px rgba(0,0,0,0.1)' }}>
        <h1 style={{ textAlign: 'center', marginBottom: 24 }}>MedAgent</h1>
        <div style={{ textAlign: 'center', marginBottom: 20 }}>
          <span style={{ fontWeight: mode === 'login' ? 600 : 400, cursor: 'pointer', padding: '8px 20px', borderBottom: mode === 'login' ? '2px solid #1677ff' : '2px solid transparent', color: mode === 'login' ? '#1677ff' : '#999' }} onClick={() => setMode('login')}>登录</span>
          <span style={{ fontWeight: mode === 'register' ? 600 : 400, cursor: 'pointer', padding: '8px 20px', borderBottom: mode === 'register' ? '2px solid #1677ff' : '2px solid transparent', color: mode === 'register' ? '#1677ff' : '#999' }} onClick={() => setMode('register')}>注册</span>
        </div>
        {error && <div style={{ color: error.includes('成功') ? '#52c41a' : '#ff4d4f', marginBottom: 16, textAlign: 'center', fontSize: 14 }}>{error}</div>}
        <input
          type="text"
          placeholder="用户名"
          value={username}
          onChange={(e) => setUsername(e.target.value)}
          style={{ width: '100%', padding: '8px 12px', marginBottom: 16, border: '1px solid #d9d9d9', borderRadius: 6, fontSize: 14, boxSizing: 'border-box' }}
          required
        />
        <input
          type="password"
          placeholder="密码"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          style={{ width: '100%', padding: '8px 12px', marginBottom: 16, border: '1px solid #d9d9d9', borderRadius: 6, fontSize: 14, boxSizing: 'border-box' }}
          required
        />
        {mode === 'register' && (
          <>
            <input
              type="text"
              placeholder="显示名称（如：张三）"
              value={name}
              onChange={(e) => setName(e.target.value)}
              style={{ width: '100%', padding: '8px 12px', marginBottom: 16, border: '1px solid #d9d9d9', borderRadius: 6, fontSize: 14, boxSizing: 'border-box' }}
              required
            />
            <select
              value={role}
              onChange={(e) => setRole(e.target.value as 'patient' | 'doctor')}
              style={{ width: '100%', padding: '8px 12px', marginBottom: 16, border: '1px solid #d9d9d9', borderRadius: 6, fontSize: 14, boxSizing: 'border-box', background: '#fff' }}
            >
              <option value="patient">患者</option>
              <option value="doctor">医生</option>
            </select>
          </>
        )}
        <button
          type="submit"
          disabled={loading}
          style={{ width: '100%', padding: '10px 0', background: '#1677ff', color: '#fff', border: 'none', borderRadius: 6, fontSize: 16, cursor: loading ? 'not-allowed' : 'pointer', opacity: loading ? 0.7 : 1 }}
        >
          {loading ? '处理中...' : mode === 'login' ? '登录' : '注册'}
        </button>
      </form>
    </div>
  )
}
