import { useState } from 'react'

const now = () => new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })

const initialMessages = [
  { role: 'assistant', content: 'Welcome to Kaspa Chatbot. Ask me about KAS, blocks, DAG, or ecosystem tools.', timestamp: now() },
  { role: 'user', content: 'What is Kaspa?', timestamp: now() },
  { role: 'assistant', content: 'Kaspa is a proof-of-work cryptocurrency implementing the GhostDAG protocol for high block throughput and fast confirmations.', timestamp: now() },
]

const initialConversations = [
  { id: '1', title: 'Onboarding', preview: 'Welcome to Kaspa Chatbot...', updatedAt: 'just now' },
  { id: '2', title: 'Kaspa 101', preview: 'Kaspa is a PoW coin with GhostDAG...', updatedAt: '1h' },
]

export function useChat() {
  const [messages, setMessages] = useState(initialMessages)
  const [conversations, setConversations] = useState(initialConversations)
  const [active, setActive] = useState('1')

  const sendMessage = async (text) => {
    const ts = now()
    setMessages(prev => [...prev, { role: 'user', content: text, timestamp: ts }])
    try {
      const res = await fetch('http://localhost:8000/ask', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question: text })
      })
      const data = await res.json()
      setMessages(prev => [...prev, { role: 'assistant', content: data.answer || 'No answer', timestamp: now() }])
    } catch (err) {
      setMessages(prev => [...prev, { role: 'assistant', content: 'Error contacting backend', timestamp: now() }])
    }
  }

  const setActiveConversation = (id) => {
    setActive(id)
    // Placeholder: In real app load messages for this conversation
  }

  return { messages, sendMessage, conversations, setActiveConversation }
}
