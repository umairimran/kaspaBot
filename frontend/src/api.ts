import axios from 'axios'
import type { AskResponse } from './types'

// Resolve base URL with sensible fallbacks for dev if env is missing
const resolvedBaseURL =
  (import.meta as any)?.env?.VITE_API_URL ||
  (typeof import.meta !== 'undefined' && (import.meta as any)?.env?.VITE_API_URL) ||
  (typeof window !== 'undefined'
    ? `${window.location.protocol}//${window.location.hostname}:8001`
    : 'http://127.0.0.1:8001')

const api = axios.create({
  baseURL: resolvedBaseURL,
  headers: { 'Content-Type': 'application/json' },
  timeout: 30000,
})

export async function ask(question: string, conversationId?: string): Promise<AskResponse> {
  const { data } = await api.post<AskResponse>('/ask', { 
    question,
    conversation_id: conversationId,
    user_id: 'temp_user'
  })
  return data
}

export default api


