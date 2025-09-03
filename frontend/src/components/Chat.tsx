import React, { useEffect, useRef, useState } from 'react'
import type { Citation } from '../types'

function QuickActions({ onQuickQuestion }: { onQuickQuestion: (q: string) => void }) {
  const quickQuestions = [
    "What is Kaspa's consensus mechanism?",
    "How fast are Kaspa transactions?",
    "What makes Kaspa different from Bitcoin?",
    "How does Kaspa mining work?",
    "What is the GHOSTDAG protocol?"
  ]

  return (
    <div className="max-w-4xl mx-auto p-4">
      <div className="text-center mb-4">
        <h3 className="text-lg font-medium text-kaspa mb-2">Quick Questions</h3>
        <p className="text-sm text-slate-400">Get started with these popular questions:</p>
      </div>
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
        {quickQuestions.map((question, idx) => (
          <button
            key={idx}
            onClick={() => onQuickQuestion(question)}
            className="p-3 text-left rounded-xl bg-surface/40 border border-kaspa/20 hover:border-kaspa/40 hover:bg-surface/60 transition-all text-sm"
          >
            {question}
          </button>
        ))}
      </div>
    </div>
  )
}

interface Message {
  id: string
  role: 'user' | 'assistant'
  content: string
  citations?: Citation[]
}

interface Props {
  messages: Message[]
  input: string
  setInput: (input: string) => void
  onSend: () => void
  loading: boolean
  onKeyDown: (e: React.KeyboardEvent<HTMLInputElement | HTMLTextAreaElement>) => void
  lastQ?: string
  lastA?: string
  postToTwitter?: () => void
  tweetStatus?: string
}

function Citations({ citations }: { citations: Citation[] }) {
  return (
    <div className="mt-4 pt-3 border-t border-kaspa/20">
      <div className="text-xs text-slate-400 mb-2 font-medium">Sources:</div>
      <div className="space-y-2">
        {citations.slice(0, 3).map((citation, idx) => (
          <div key={idx} className="text-xs">
            <a
              href={citation.url}
              target="_blank"
              rel="noopener noreferrer"
              className="text-kaspa hover:text-kaspa/80 font-medium transition-colors"
            >
              {citation.filename || new URL(citation.url).hostname}
            </a>
            {citation.section && (
              <span className="text-slate-400 ml-1">({citation.section})</span>
            )}
          </div>
        ))}
      </div>
    </div>
  )
}

function Thinking() {
  return (
    <div className="flex items-center gap-2 text-slate-400">
      <div className="flex gap-1">
        <div className="w-2 h-2 bg-kaspa rounded-full animate-pulse"></div>
        <div className="w-2 h-2 bg-kaspa rounded-full animate-pulse" style={{ animationDelay: '0.1s' }}></div>
        <div className="w-2 h-2 bg-kaspa rounded-full animate-pulse" style={{ animationDelay: '0.2s' }}></div>
      </div>
      <span className="text-sm">KaspaBot is thinking...</span>
    </div>
  )
}

export default function Chat({ 
  messages, 
  input, 
  setInput, 
  onSend, 
  loading, 
  onKeyDown,
  lastQ,
  lastA,
  postToTwitter,
  tweetStatus
}: Props) {
  const listRef = useRef<HTMLDivElement>(null)
  const endRef = useRef<HTMLDivElement>(null)
  const [showQuickActions, setShowQuickActions] = useState(true)

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, loading])

  const handleQuickQuestion = (question: string) => {
    setInput(question)
    setShowQuickActions(false)
    // Trigger send after a brief delay to let the input update
    setTimeout(() => onSend(), 100)
  }

  const canSend = input.trim() && !loading

  const handleSendClick = () => {
    setShowQuickActions(false)
    onSend()
  }

  return (
    <div className="flex flex-col h-[600px]">
      {/* Quick Actions */}
      {showQuickActions && messages.length <= 1 && (
        <QuickActions onQuickQuestion={handleQuickQuestion} />
      )}

      {/* Messages */}
      <div ref={listRef} className="flex-1 overflow-y-auto p-4 space-y-6">
        {messages.map(m => (
          <div
            key={m.id}
            className={`max-w-4xl mx-auto animate-fadeInUp ${m.role === 'user' ? 'text-black' : 'text-slate-200'}`}
          >
            <div
              className={`w-fit px-6 py-4 rounded-2xl shadow-lg ${
                m.role === 'user'
                  ? 'bg-gradient-to-r from-kaspa to-kaspa/80 text-black ml-auto rounded-br-sm'
                  : 'glass-card text-slate-200 rounded-bl-sm max-w-full'
              }`}
            >
              <div className="whitespace-pre-wrap leading-relaxed">{m.content}</div>
              
              {/* Display sources for assistant messages */}
              {m.role === 'assistant' && m.citations && (
                <Citations citations={m.citations} />
              )}
            </div>
          </div>
        ))}

        {loading && (
          <div className="max-w-4xl mx-auto animate-fadeInUp">
            <div className="glass-card w-fit px-6 py-4 rounded-2xl">
              <Thinking />
            </div>
          </div>
        )}

        <div ref={endRef} />
      </div>

      {/* Enhanced Input Area */}
      <div className="sticky bottom-0 left-0 right-0 bg-background/80 backdrop-blur border-t border-kaspa/10">
        <div className="max-w-4xl mx-auto p-4">
          <div className="flex gap-3 items-end">
            <div className="flex-1">
              <textarea
                value={input}
                onChange={e => setInput(e.target.value)}
                onKeyDown={onKeyDown}
                placeholder="Ask me anything about Kaspa..."
                rows={1}
                className="w-full rounded-xl bg-surface/80 border border-kaspa/20 px-4 py-3 outline-none focus:border-kaspa/60 focus:shadow-glow resize-none min-h-[48px] max-h-32"
                style={{ 
                  height: 'auto',
                  overflow: 'hidden'
                }}
                onInput={(e) => {
                  const target = e.target as HTMLTextAreaElement
                  target.style.height = 'auto'
                  target.style.height = target.scrollHeight + 'px'
                }}
              />
            </div>
            <button
              disabled={!canSend}
              onClick={handleSendClick}
              className="px-6 py-3 rounded-xl bg-gradient-to-r from-kaspa to-kaspa/80 text-black font-medium disabled:opacity-50 disabled:cursor-not-allowed shadow-glow hover:shadow-[0_0_30px_rgba(57,208,216,0.55)] transition-all transform hover:scale-105 disabled:transform-none"
            >
              Send
            </button>
          </div>
          
          {/* Twitter Button */}
          {lastQ && lastA && postToTwitter && (
            <div className="mt-3 flex justify-center">
              <button
                onClick={postToTwitter}
                className="flex items-center gap-2 px-4 py-2 rounded-xl bg-blue-500/20 border border-blue-500/30 text-blue-400 font-medium hover:bg-blue-500/30 hover:border-blue-500/50 transition-all"
              >
                <span>🐦</span>
                <span>Share last Q&A on Twitter</span>
              </button>
            </div>
          )}
          
          {tweetStatus && (
            <div className="mt-2 text-center">
              <div className={`text-sm px-3 py-1 rounded-full inline-block ${
                tweetStatus.includes('Failed') 
                  ? 'bg-red-500/20 text-red-400 border border-red-500/30' 
                  : 'bg-green-500/20 text-green-400 border border-green-500/30'
              }`}>
                {tweetStatus}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
