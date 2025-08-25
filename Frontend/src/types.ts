export interface Citation {
  url: string
  label: string
}

export interface AskResponse {
  answer: string
  citations: Citation[]
}

export interface ChatTurn {
  id: string
  role: 'user' | 'assistant' | 'system'
  content: string
  citations?: Citation[]
  error?: boolean
}


