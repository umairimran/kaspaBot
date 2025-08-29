import { useState, useRef, useEffect } from 'react'
import { motion } from 'framer-motion'
import ChatMessage from './ChatMessage.jsx'

export default function ChatWindow({ messages = [], onSend }) {
  const [input, setInput] = useState('')
  const endRef = useRef(null)

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const submit = (e) => {
    e.preventDefault()
    const text = input.trim()
    if (!text) return
    onSend?.(text)
    setInput('')
  }

  return (
    <div className="card h-[70vh] lg:h-[calc(100vh-6rem)] flex flex-col">
      <div className="border-b border-slate-800/70 px-4 py-3 flex items-center justify-between">
        <div>
          <h2 className="text-sm font-semibold text-slate-300">Chat</h2>
          <p className="text-xs text-slate-500">Kaspa knowledge-base ready</p>
        </div>
        <div className="text-xs text-slate-500">Experimental</div>
      </div>

      <div className="flex-1 overflow-auto p-4 space-y-3">
        {messages.map((m, idx) => (
          <motion.div key={idx} initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }}>
            <ChatMessage role={m.role} content={m.content} timestamp={m.timestamp} />
          </motion.div>
        ))}
        <div ref={endRef} />
      </div>

      <form onSubmit={submit} className="border-t border-slate-800/70 p-3 bg-slate-900/80">
        <div className="flex items-end gap-2">
          <textarea
            className="input min-h-[48px] max-h-40 flex-1 resize-y rounded-2xl px-4 py-3 text-base bg-white/90 text-kaspa-800 placeholder-slate-400 shadow focus:ring-2 focus:ring-kaspa-400"
            rows="1"
            placeholder="Ask about Kaspa..."
            value={input}
            onChange={(e) => setInput(e.target.value)}
            style={{ fontSize: '1.1rem' }}
          />
          <button type="submit" className="rounded-full bg-kaspa-500 hover:bg-kaspa-600 transition-colors h-12 w-12 flex items-center justify-center shadow-lg" aria-label="Send">
            <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" /></svg>
          </button>
        </div>
      </form>
    </div>
  )
}
