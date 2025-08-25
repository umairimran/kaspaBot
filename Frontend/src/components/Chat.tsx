import React, { useEffect, useMemo, useRef, useState } from 'react'
import { ask } from '../api'
import type { ChatTurn, Citation } from '../types'

const Greeting = "Hello! I’m KaspaBot — your guide to Kaspa cryptocurrency. Ask me anything about Kaspa."

function Citations({ citations }: { citations: Citation[] }) {
  if (!citations || citations.length === 0) return null
  return (
    <div className="mt-3 flex flex-wrap gap-2">
      {citations.map((c, i) => (
        <a
          key={i}
          href={c.url}
          target="_blank"
          rel="noopener noreferrer"
          className="text-xs px-2 py-1 rounded-full border border-kaspa/40 text-kaspa hover:shadow-glow hover:border-kaspa transition-shadow"
        >
          {c.label || new URL(c.url).hostname}
        </a>
      ))}
    </div>
  )
}

function Thinking() {
  return (
    <div className="text-sm text-slate-300 flex items-center gap-2">
      <span className="relative inline-flex w-2 h-2 rounded-full bg-kaspa/70 animate-pulseDots" />
      <span>Thinking...</span>
    </div>
  )
}

export default function Chat() {
  const [input, setInput] = useState('')
  const [messages, setMessages] = useState<ChatTurn[]>(() => [
    { id: crypto.randomUUID(), role: 'assistant', content: Greeting },
  ])
  const [loading, setLoading] = useState(false)
  const listRef = useRef<HTMLDivElement>(null)
  const endRef = useRef<HTMLDivElement>(null)

  const scrollToBottom = () => {
    endRef.current?.scrollIntoView({ behavior: 'smooth', block: 'end' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages, loading])

  const canSend = useMemo(() => input.trim().length > 0 && !loading, [input, loading])

  async function onSend() {
    const q = input.trim()
    if (!q) return
    setInput('')

    const userMsg: ChatTurn = { id: crypto.randomUUID(), role: 'user', content: q }
    setMessages(prev => [...prev, userMsg])
    setLoading(true)
    try {
      const res = await ask(q)
      const assistant: ChatTurn = {
        id: crypto.randomUUID(),
        role: 'assistant',
        content: res.answer,
        citations: res.citations || [],
      }
      setMessages(prev => [...prev, assistant])
    } catch (err) {
      const assistant: ChatTurn = {
        id: crypto.randomUUID(),
        role: 'assistant',
        content: 'Sorry, something went wrong while contacting the Kaspa RAG API.',
        error: true,
      }
      setMessages(prev => [...prev, assistant])
    } finally {
      setLoading(false)
    }
  }

  function onKeyDown(e: React.KeyboardEvent<HTMLInputElement>) {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      if (canSend) onSend()
    }
  }

  return (
    <div className="flex flex-col h-full">
      {/* Messages */}
      <div ref={listRef} className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.map(m => (
          <div
            key={m.id}
            className={`max-w-3xl mx-auto animate-fadeInUp ${m.role === 'user' ? 'text-black' : 'text-slate-200'}`}
          >
            <div
              className={`w-fit px-4 py-3 rounded-2xl shadow-lg ${
                m.role === 'user'
                  ? 'bg-kaspa text-black ml-auto rounded-br-sm'
                  : 'glass-card text-slate-200 rounded-bl-sm'
              }`}
            >
              <div className="whitespace-pre-wrap leading-relaxed">{m.content}</div>
            </div>
          </div>
        ))}

        {loading && (
          <div className="max-w-3xl mx-auto animate-fadeInUp">
            <div className="glass-card w-fit px-4 py-3 rounded-2xl"><Thinking /></div>
          </div>
        )}

        <div ref={endRef} />
      </div>

      {/* Input */}
      <div className="sticky bottom-0 left-0 right-0 bg-background/80 backdrop-blur border-t border-kaspa/10">
        <div className="max-w-3xl mx-auto p-3 flex gap-2">
          <input
            value={input}
            onChange={e => setInput(e.target.value)}
            onKeyDown={onKeyDown}
            placeholder="Ask a question about Kaspa..."
            className="flex-1 rounded-xl bg-surface/80 border border-kaspa/20 px-4 py-3 outline-none focus:border-kaspa/60 focus:shadow-glow"
          />
          <button
            disabled={!canSend}
            onClick={onSend}
            className="px-5 py-3 rounded-xl bg-kaspa text-black font-medium disabled:opacity-50 disabled:cursor-not-allowed shadow-glow hover:shadow-[0_0_30px_rgba(57,208,216,0.55)] transition-shadow"
          >
            Send
          </button>
        </div>
      </div>
    </div>
  )
}


