import { useState, useRef, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuthStore } from '../../stores/authStore'
import { useChatStore } from '../../stores/chatStore'
import { useVoiceStore } from '../../stores/voiceStore'
import { streamChat, fetchChatDetail } from '../../api/chat'
import { synthesizeSpeech } from '../../api/voice'
import ChatBubble from '../../components/shared/ChatBubble'
import VoiceInput from '../../components/patient/VoiceInput'
import ReportUploader from '../../components/patient/ReportUploader'
import ReasoningChain from '../../components/shared/ReasoningChain'
import type { ChatMessage } from '../../types'

export default function PatientChat() {
  const [input, setInput] = useState('')
  const [sending, setSending] = useState(false)
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const navigate = useNavigate()

  const token = useAuthStore((s) => s.token)
  const user = useAuthStore((s) => s.user)
  const logout = useAuthStore((s) => s.logout)
  const { messages, isStreaming, currentStreaming, currentSources, currentReasoningSteps, addMessage, setStreaming, appendStreaming, setSources, setReasoningSteps, finishStreaming } = useChatStore()
  const { setPlaying } = useVoiceStore()
  const [speakingMsgId, setSpeakingMsgId] = useState<string | null>(null)

  useEffect(() => {
    if (!token) { navigate('/login'); return }
    // Load old messages from backend on mount
    useChatStore.getState().clear()
    fetchChatDetail(token, 'default').then((data) => {
      data.messages.forEach((m) => {
        addMessage({
          id: String(m.id),
          role: m.role as 'user' | 'assistant',
          content: m.content,
          timestamp: m.created_at,
        })
      })
    }).catch(() => {
      // No history yet, that's fine
    })
  }, [token, navigate])

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, currentStreaming])

  const handleSend = async () => {
    const text = input.trim()
    if (!text || sending || !token) return

    setInput('')
    setSending(true)
    setStreaming(true)

    const userMsg: ChatMessage = {
      id: `user_${Date.now()}`,
      role: 'user',
      content: text,
      timestamp: new Date().toISOString(),
    }
    addMessage(userMsg)

    try {
      for await (const chunk of streamChat(text, 'default', token)) {
        if (chunk.type === 'chunk' && chunk.content) {
          appendStreaming(chunk.content)
        } else if (chunk.type === 'sources' && chunk.sources) {
          setSources(chunk.sources)
        } else if (chunk.type === 'reasoning_steps' && chunk.steps) {
          setReasoningSteps(chunk.steps)
        } else if (chunk.type === 'done') {
          finishStreaming()
        } else if (chunk.type === 'error') {
          throw new Error(chunk.message || 'Unknown error')
        }
      }
    } catch (err) {
      console.error('Chat error:', err)
      finishStreaming()
    } finally {
      setSending(false)
    }
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  const handleSpeak = async (msgId: string, content: string) => {
    if (speakingMsgId) return
    setSpeakingMsgId(msgId)
    try {
      const blob = await synthesizeSpeech(content)
      const url = URL.createObjectURL(blob)
      const audio = new Audio(url)
      audio.onended = () => {
        URL.revokeObjectURL(url)
        setSpeakingMsgId(null)
        setPlaying(false)
      }
      setPlaying(true)
      audio.play()
    } catch {
      setSpeakingMsgId(null)
    }
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
        <h2 style={{ margin: 0, fontSize: 18, color: '#1677ff' }}>MedAgent · 患者助手</h2>
        <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
          <span style={{ color: '#666', fontSize: 14 }}>{user?.name}</span>
          <button onClick={() => navigate('/patient/history')} style={{ padding: '4px 12px', border: '1px solid #d9d9d9', borderRadius: 4, background: '#fff', cursor: 'pointer', fontSize: 13, color: '#1677ff' }}>
            📋 对话历史
          </button>
          <button onClick={() => { logout(); navigate('/login') }} style={{ padding: '4px 12px', border: '1px solid #d9d9d9', borderRadius: 4, background: '#fff', cursor: 'pointer', fontSize: 13 }}>
            退出
          </button>
        </div>
      </header>

      {/* Messages */}
      <div style={{ flex: 1, overflowY: 'auto', padding: '24px 16px' }}>
        <ReportUploader />
        {currentReasoningSteps.length > 0 && (
          <ReasoningChain steps={currentReasoningSteps} />
        )}
        {messages.map((msg) => (
          <div key={msg.id}>
            <ChatBubble message={msg} />
            {msg.role === 'assistant' && msg.content && (
              <button
                onClick={() => handleSpeak(msg.id, msg.content)}
                disabled={speakingMsgId === msg.id}
                style={{
                  marginLeft: 48,
                  marginTop: -4,
                  marginBottom: 12,
                  padding: '2px 8px',
                  border: '1px solid #d9d9d9',
                  borderRadius: 4,
                  background: '#fff',
                  cursor: speakingMsgId ? 'not-allowed' : 'pointer',
                  fontSize: 12,
                  color: '#1677ff',
                }}
              >
                {speakingMsgId === msg.id ? '播放中...' : '🔊 播放语音'}
              </button>
            )}
          </div>
        ))}
        {isStreaming && currentStreaming && (
          <ChatBubble
            message={{
              id: 'streaming',
              role: 'assistant',
              content: currentStreaming,
              sources: currentSources,
              timestamp: new Date().toISOString(),
            }}
          />
        )}
        {sending && !currentStreaming && (
          <div style={{ textAlign: 'center', color: '#999', padding: 12 }}>正在思考...</div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Suggested questions */}
      <div style={{ padding: '8px 24px', background: '#f5f5f5', borderTop: '1px solid #e8e8e8' }}>
        <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
            {['我头痛好几天了怎么办', '感冒了该吃什么药', '血压偏高要注意什么', '血常规报告怎么看', '糖尿病饮食要注意什么'].map((q) => (
              <button
                key={q}
                onClick={() => { setInput(q); }}
                style={{
                  padding: '6px 14px',
                  border: '1px solid #b7eb8f',
                  borderRadius: 16,
                  background: '#f6ffed',
                  cursor: 'pointer',
                  fontSize: 13,
                  color: '#389e0d',
                  whiteSpace: 'nowrap',
                }}
              >
                {q}
              </button>
            ))}
          </div>
      </div>
      <div style={{ background: '#fff', padding: '16px 24px', borderTop: '1px solid #e8e8e8' }}>
        <VoiceInput />
        <div style={{ display: 'flex', gap: 12, marginTop: 8 }}>
          <textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="输入您的健康问题..."
            rows={2}
            disabled={sending}
            style={{
              flex: 1,
              padding: '10px 12px',
              border: '1px solid #d9d9d9',
              borderRadius: 8,
              fontSize: 14,
              resize: 'none',
              fontFamily: 'inherit',
            }}
          />
          <button
            onClick={handleSend}
            disabled={sending || !input.trim()}
            style={{
              padding: '0 24px',
              background: sending ? '#91caff' : '#1677ff',
              color: '#fff',
              border: 'none',
              borderRadius: 8,
              fontSize: 15,
              cursor: sending ? 'not-allowed' : 'pointer',
              whiteSpace: 'nowrap',
            }}
          >
            {sending ? '发送中' : '发送'}
          </button>
        </div>
      </div>
    </div>
  )
}
