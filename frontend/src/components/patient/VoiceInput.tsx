import { useRef, useCallback } from 'react'
import { useVoiceStore } from '../../stores/voiceStore'
import { transcribeAudio } from '../../api/voice'

export default function VoiceInput() {
  const mediaRecorder = useRef<MediaRecorder | null>(null)
  const chunks = useRef<Blob[]>([])

  const { isRecording, state, transcript, startRecording, stopRecording, setTranscript, clearTranscript } = useVoiceStore()

  const onStart = useCallback(async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
      const recorder = new MediaRecorder(stream, { mimeType: 'audio/webm' })
      mediaRecorder.current = recorder
      chunks.current = []

      recorder.ondataavailable = (e) => {
        if (e.data.size > 0) chunks.current.push(e.data)
      }

      recorder.onstop = async () => {
        stream.getTracks().forEach((t) => t.stop())
        const blob = new Blob(chunks.current, { type: 'audio/webm' })
        stopRecording(blob)

        try {
          const result = await transcribeAudio(blob)
          setTranscript(result.text)
        } catch {
          setTranscript('语音识别失败，请重试')
        }
      }

      recorder.start()
      startRecording()
    } catch {
      alert('无法访问麦克风，请检查浏览器权限设置')
    }
  }, [startRecording, stopRecording, setTranscript])

  const onStop = useCallback(() => {
    if (mediaRecorder.current && mediaRecorder.current.state === 'recording') {
      mediaRecorder.current.stop()
    }
  }, [])

  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
      {transcript && (
        <div style={{ flex: 1, padding: '4px 8px', background: '#f0f5ff', borderRadius: 6, fontSize: 13, color: '#1677ff' }}>
          {transcript}
          <button
            onClick={clearTranscript}
            style={{ marginLeft: 8, padding: 0, border: 'none', background: 'none', color: '#999', cursor: 'pointer', fontSize: 12 }}
          >
            ✕
          </button>
        </div>
      )}

      <button
        onMouseDown={onStart}
        onMouseUp={onStop}
        onMouseLeave={onStop}
        onTouchStart={onStart}
        onTouchEnd={onStop}
        disabled={state === 'transcribing'}
        style={{
          width: 40,
          height: 40,
          borderRadius: '50%',
          border: 'none',
          background: isRecording ? '#ff4d4f' : state === 'transcribing' ? '#d9d9d9' : '#1677ff',
          color: '#fff',
          fontSize: 20,
          cursor: state === 'transcribing' ? 'not-allowed' : 'pointer',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          flexShrink: 0,
        }}
        title="按住说话"
      >
        {isRecording ? '⏹' : '🎤'}
      </button>
    </div>
  )
}
