import { useState } from 'react'
import type { ReActStep } from '../../types'

interface Props {
  steps: ReActStep[]
}

const LABELS: Record<string, string> = {
  thought: '思考',
  action: '行动',
  action_input: '行动输入',
  observation: '观察',
}

const COLORS: Record<string, { bg: string; text: string }> = {
  thought: { bg: '#f0f5ff', text: '#1677ff' },
  action: { bg: '#fff7e6', text: '#fa8c16' },
  action_input: { bg: '#f6ffed', text: '#52c41a' },
  observation: { bg: '#f9f0ff', text: '#722ed1' },
}

export default function ReasoningChain({ steps }: Props) {
  const [expanded, setExpanded] = useState(false)

  if (!steps || steps.length === 0) return null

  return (
    <div
      style={{
        border: '1px solid #e8e8e8',
        borderRadius: 8,
        marginBottom: 12,
        overflow: 'hidden',
      }}
    >
      <div
        onClick={() => setExpanded(!expanded)}
        style={{
          padding: '8px 16px',
          background: '#fafafa',
          cursor: 'pointer',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          fontSize: 13,
          fontWeight: 600,
          color: '#555',
          userSelect: 'none',
        }}
      >
        <span>{'推理链 (' + steps.length + ' 步)'}</span>
        <span style={{ fontSize: 11 }}>{expanded ? '收起' : '展开'}</span>
      </div>

      {expanded && (
        <div style={{ padding: '8px 16px 12px' }}>
          {steps.map((step, i) => (
            <div
              key={i}
              style={{
                marginBottom: i < steps.length - 1 ? 12 : 0,
                padding: '8px 12px',
                background: '#fff',
                border: '1px solid #f0f0f0',
                borderRadius: 6,
              }}
            >
              <div style={{ fontSize: 12, fontWeight: 600, color: '#999', marginBottom: 4 }}>
                {'第 ' + (i + 1) + ' 步'}
              </div>
              {(['thought', 'action', 'action_input', 'observation'] as const).map((field) => {
                const value =
                  field === 'action_input'
                    ? JSON.stringify(step[field], null, 2)
                    : String(step[field] || '')
                if (!value || value === '{}') return null
                const c = COLORS[field]
                return (
                  <div key={field} style={{ marginBottom: 4 }}>
                    <span
                      style={{
                        display: 'inline-block',
                        background: c.bg,
                        color: c.text,
                        padding: '0 6px',
                        borderRadius: 3,
                        fontSize: 11,
                        fontWeight: 600,
                        marginRight: 6,
                      }}
                    >
                      {LABELS[field]}
                    </span>
                    <span style={{ fontSize: 13, color: '#333', whiteSpace: 'pre-wrap' }}>
                      {value}
                    </span>
                  </div>
                )
              })}
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
