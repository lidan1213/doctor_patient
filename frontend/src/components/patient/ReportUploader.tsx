import { useState, useCallback } from 'react'
import { uploadReport, interpretReport } from '../../api/report'
import type { ReportInterpretation } from '../../types'

export default function ReportUploader() {
  const [uploading, setUploading] = useState(false)
  const [interpreting, setInterpreting] = useState(false)
  const [dragOver, setDragOver] = useState(false)
  const [result, setResult] = useState<ReportInterpretation | null>(null)
  const [error, setError] = useState('')

  const handleFile = useCallback(async (file: File) => {
    setError('')
    setResult(null)
    setUploading(true)

    try {
      const uploaded = await uploadReport(file)
      setInterpreting(true)

      try {
        const interpretation = await interpretReport(uploaded.report_id)
        setResult(interpretation)
      } catch {
        setError('报告解读失败，请重试')
      }
    } catch {
      setError('报告上传失败，请检查文件格式')
    } finally {
      setUploading(false)
      setInterpreting(false)
    }
  }, [])

  const onDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault()
      setDragOver(false)
      const file = e.dataTransfer.files[0]
      if (file) handleFile(file)
    },
    [handleFile],
  )

  const onFileChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const file = e.target.files?.[0]
      if (file) handleFile(file)
    },
    [handleFile],
  )

  return (
    <div style={{ marginBottom: 12 }}>
      <div
        onDragOver={(e) => { e.preventDefault(); setDragOver(true) }}
        onDragLeave={() => setDragOver(false)}
        onDrop={onDrop}
        style={{
          border: `2px dashed ${dragOver ? '#1677ff' : '#d9d9d9'}`,
          borderRadius: 8,
          padding: '16px 12px',
          textAlign: 'center',
          background: dragOver ? '#e6f4ff' : '#fafafa',
          transition: 'all 0.2s',
          cursor: 'pointer',
        }}
      >
        <input
          type="file"
          accept="image/png,image/jpeg,image/gif,application/pdf"
          onChange={onFileChange}
          style={{ display: 'none' }}
          id="report-upload-input"
        />
        <label htmlFor="report-upload-input" style={{ cursor: 'pointer', display: 'block' }}>
          {uploading || interpreting ? (
            <span style={{ color: '#1677ff' }}>{uploading ? '上传中...' : 'AI 解读中...'}</span>
          ) : (
            <span style={{ color: '#999', fontSize: 13 }}>
              📄 拖拽或点击上传医学报告 (图片/PDF)
            </span>
          )}
        </label>
      </div>

      {error && (
        <div style={{ marginTop: 8, padding: '4px 8px', background: '#fff2f0', borderRadius: 4, color: '#ff4d4f', fontSize: 13 }}>
          {error}
        </div>
      )}

      {result && (
        <div style={{ marginTop: 8, padding: 12, background: '#f0f5ff', borderRadius: 8 }}>
          <div style={{ fontWeight: 600, marginBottom: 8, fontSize: 14, color: '#1677ff' }}>📋 报告解读</div>
          <div style={{ fontSize: 13, lineHeight: 1.6, color: '#333' }}>{result.summary}</div>
          {result.sections.length > 0 && (
            <div style={{ marginTop: 8 }}>
              {result.sections.map((s, i) => (
                <div key={i} style={{ marginBottom: 8 }}>
                  <div style={{ fontWeight: 600, fontSize: 13, color: '#555' }}>{s.title}</div>
                  <div style={{ fontSize: 13, color: '#666', lineHeight: 1.5 }}>{s.content}</div>
                </div>
              ))}
            </div>
          )}
          <div style={{ marginTop: 8, fontSize: 11, color: '#999', fontStyle: 'italic' }}>{result.disclaimer}</div>
        </div>
      )}
    </div>
  )
}
