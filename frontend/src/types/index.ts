export interface User {
  id: number
  username: string
  role: 'patient' | 'doctor' | 'admin'
  name: string
}

export interface ChatMessage {
  id: string
  role: 'user' | 'assistant'
  content: string
  sources?: CitationSource[]
  timestamp: string
}

export interface CitationSource {
  id: string
  title: string
  type: 'guideline' | 'literature' | 'drug' | 'education'
  url?: string
  evidence_level?: string
  version?: string
}

export interface SSEChunk {
  type: 'chunk' | 'sources' | 'done' | 'error' | 'reasoning_steps'
  content?: string
  sources?: CitationSource[]
  message?: string
  steps?: ReActStep[]
}

export interface ReActStep {
  thought: string
  action: string
  action_input: Record<string, unknown>
  observation: string
}

export interface SearchResult {
  id: string
  title: string
  content: string
  source_type: string
  score: number
  source: CitationSource
}

export type RecordingState = 'idle' | 'recording' | 'transcribing' | 'done'

export interface ReportInfo {
  report_id: string
  filename: string
  status: string
  uploaded_at: string
}

export interface ReportSection {
  title: string
  content: string
}

export interface ReportInterpretation {
  report_id: string
  summary: string
  sections: ReportSection[]
  disclaimer: string
}

export interface ChatHistoryItem {
  session_id: string
  first_message: string
  message_count: number
  last_message_at: string
}

export interface ChatHistoryResponse {
  items: ChatHistoryItem[]
  page: number
  page_size: number
  total: number
}

export interface ChatDetailMessage {
  id: number
  role: string
  content: string
  intent?: string
  sources?: Record<string, unknown>
  created_at: string
}

export interface ChatDetailResponse {
  session_id: string
  messages: ChatDetailMessage[]
}

export interface PatientProfileData {
  user_id: number
  gender?: string
  birthday?: string
  blood_type?: string
  allergies?: string
  medical_history?: Record<string, unknown>
  personalization_config?: Record<string, unknown>
}

export interface CarePlanItemData {
  id: number
  title: string
  description?: string
  medication_schedule?: string
  follow_up_date?: string
  status: string
}

export interface CarePlanData {
  plans: CarePlanItemData[]
  total: number
}

export interface ReportInfo {
  id: number
  filename: string
  file_type: string
  ocr_text?: string
  interpretation?: string
  created_at?: string
}

export interface PatientRecordData {
  patient_id: number
  patient_name?: string
  patient_role?: string
  cases: Array<Record<string, unknown>>
  visits: Array<Record<string, unknown>>
  prescriptions: Array<Record<string, unknown>>
  reports: ReportInfo[]
}
