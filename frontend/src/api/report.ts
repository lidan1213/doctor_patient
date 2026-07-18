import type { ReportInfo, ReportInterpretation } from '../types'

const TOKEN = () => localStorage.getItem('token') || ''

export async function uploadReport(file: File): Promise<ReportInfo> {
  const formData = new FormData()
  formData.append('file', file)

  const resp = await fetch('/api/report/upload', {
    method: 'POST',
    headers: { Authorization: `Bearer ${TOKEN()}` },
    body: formData,
  })

  if (!resp.ok) {
    if (resp.status === 401) {
      localStorage.removeItem('token')
      window.location.href = '/login'
    }
    throw new Error(`Upload failed: ${resp.status}`)
  }

  return resp.json()
}

export async function interpretReport(reportId: string): Promise<ReportInterpretation> {
  const resp = await fetch(`/api/report/interpret/${encodeURIComponent(reportId)}`, {
    method: 'POST',
    headers: { Authorization: `Bearer ${TOKEN()}` },
  })

  if (!resp.ok) {
    if (resp.status === 401) {
      localStorage.removeItem('token')
      window.location.href = '/login'
    }
    throw new Error(`Interpret failed: ${resp.status}`)
  }

  return resp.json()
}
