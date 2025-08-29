export interface Citation {
  source: string
  section: string
  filename: string
  url: string
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


