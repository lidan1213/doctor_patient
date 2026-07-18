import type { ChatMessage } from '../../types'
import MarkdownRenderer from './MarkdownRenderer'
import CitationCard from './CitationCard'

interface Props {
  message: ChatMessage
}

export default function ChatBubble({ message }: Props) {
  const isUser = message.role === 'user'

  return (
    <div
      style={{
        display: 'flex',
        justifyContent: isUser ? 'flex-end' : 'flex-start',
        marginBottom: 16,
      }}
    >
      <div
        style={{
          maxWidth: '75%',
          background: isUser ? '#1677ff' : '#f5f5f5',
          color: isUser ? '#fff' : '#333',
          borderRadius: 12,
          padding: '12px 16px',
          borderBottomRightRadius: isUser ? 4 : 12,
          borderBottomLeftRadius: isUser ? 12 : 4,
        }}
      >
        {isUser ? (
          <span>{message.content}</span>
        ) : (
          <>
            <MarkdownRenderer content={message.content} />
            {message.sources && message.sources.length > 0 && (
              <div style={{ marginTop: 12, borderTop: '1px solid #e8e8e8', paddingTop: 8 }}>
                <div style={{ fontSize: 12, color: '#999', marginBottom: 6 }}>引用来源:</div>
                {message.sources.map((s, i) => (
                  <CitationCard key={i} source={s} />
                ))}
              </div>
            )}
          </>
        )}
      </div>
    </div>
  )
}
