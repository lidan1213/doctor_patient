import type { PatientRecordData } from '../types'

const TOKEN = () => localStorage.getItem('token') || ''

export async function fetchPatientRecord(patientId: number): Promise<PatientRecordData> {
  const resp = await fetch(`/api/doctor/patient/${patientId}`, {
    headers: { Authorization: `Bearer ${TOKEN()}` },
  })
  if (!resp.ok) {
    if (resp.status === 401) { localStorage.removeItem('token'); window.location.href = '/login' }
    throw new Error(`Fetch patient record failed: ${resp.status}`)
  }
  return resp.json()
}
