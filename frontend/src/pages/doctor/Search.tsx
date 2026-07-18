import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuthStore } from '../../stores/authStore'
import { useSearchStore } from '../../stores/searchStore'
import { search } from '../../api/search'
import SearchPanel from '../../components/doctor/SearchPanel'

export default function DoctorSearch() {
  const [input, setInput] = useState('')
  const navigate = useNavigate()

  const token = useAuthStore((s) => s.token)
  const user = useAuthStore((s) => s.user)
  const logout = useAuthStore((s) => s.logout)
  const { results, sources, loading, setQuery, setResults, setLoading } = useSearchStore()

  useEffect(() => {
    if (!token) navigate('/login')
  }, [token, navigate])

  const handleSearch = async () => {
    const q = input.trim()
    if (!q || !token) return
    setQuery(q)
    setLoading(true)
    try {
      const data = await search(q, token)
      setResults(data.results, data.sources)
    } catch (err) {
      console.error('Search error:', err)
    } finally {
      setLoading(false)
    }
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') handleSearch()
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100vh', background: '#f5f5f5' }}>
      {/* Header */}
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
        <h2 style={{ margin: 0, fontSize: 18, color: '#52c41a' }}>MedAgent · 医生工作站</h2>
        <div>
          <span style={{ marginRight: 16, color: '#666' }}>{user?.name} · {user?.role === 'doctor' ? '医生' : ''}</span>
          <button onClick={() => { logout(); navigate('/login') }} style={{ padding: '4px 12px', border: '1px solid #d9d9d9', borderRadius: 4, background: '#fff', cursor: 'pointer' }}>
            退出
          </button>
        </div>
      </header>

      {/* Search input */}
      <div style={{ background: '#fff', padding: '16px 24px', borderBottom: '1px solid #e8e8e8' }}>
        <div style={{ display: 'flex', gap: 12, marginBottom: 12, alignItems: 'center' }}>
          <span style={{ fontSize: 14, fontWeight: 600, color: '#333' }}>知识库检索</span>
          <span style={{ fontSize: 12, color: '#999' }}>｜</span>
          <button
            onClick={() => navigate('/doctor/patient/1')}
            style={{ padding: '4px 12px', background: '#e6f7ff', border: '1px solid #91d5ff', borderRadius: 4, cursor: 'pointer', fontSize: 13, color: '#1890ff' }}
          >
            查看测试患者档案 →
          </button>
        </div>
        <div style={{ display: 'flex', gap: 12 }}>
          <input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="输入医学检索关键词，如：二甲双胍肾功能不全剂量调整..."
            style={{
              flex: 1,
              padding: '10px 12px',
              border: '1px solid #d9d9d9',
              borderRadius: 8,
              fontSize: 14,
            }}
          />
          <button
            onClick={handleSearch}
            disabled={loading || !input.trim()}
            style={{
              padding: '0 24px',
              background: '#52c41a',
              color: '#fff',
              border: 'none',
              borderRadius: 8,
              fontSize: 15,
              cursor: 'pointer',
            }}
          >
            检索
          </button>
        </div>

        {/* Filters */}
        <div style={{ display: 'flex', gap: 12, marginTop: 12 }}>
          <select style={{ padding: '4px 8px', border: '1px solid #d9d9d9', borderRadius: 4, fontSize: 13 }}>
            <option value="">全部类型</option>
            <option value="guideline">临床指南</option>
            <option value="literature">医学文献</option>
            <option value="drug">药品信息</option>
          </select>
          <select style={{ padding: '4px 8px', border: '1px solid #d9d9d9', borderRadius: 4, fontSize: 13 }}>
            <option value="">全部证据等级</option>
            <option value="A">A级 · 指南推荐</option>
            <option value="B">B级 · Meta分析</option>
            <option value="C">C级 · RCT</option>
          </select>
        </div>
      </div>

      {/* Results */}
      <div style={{ flex: 1, overflowY: 'auto' }}>
        <SearchPanel results={results} loading={loading} />
      </div>

      {/* Sources summary */}
      {sources.length > 0 && (
        <div style={{ background: '#fff', padding: '12px 24px', borderTop: '1px solid #e8e8e8', fontSize: 12, color: '#999' }}>
          共检索到 {results.length} 条结果，引用来源 {sources.length} 条
        </div>
      )}
    </div>
  )
}
