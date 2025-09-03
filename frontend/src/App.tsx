import React, { useState } from 'react'
import Chat from './components/Chat'
import kaspaLogo from './images/kaspa_logo.jpeg'
import { ask } from './api'
import type { Citation } from './types'

interface Message {
  id: string
  role: 'user' | 'assistant'
  content: string
  citations?: Citation[]
}

export default function App() {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: '1',
      role: 'assistant',
      content: `Hello! I'm KaspaBot — your AI-powered guide to Kaspa cryptocurrency. 🚀

I have access to comprehensive knowledge about Kaspa including whitepapers, technical documentation, and community insights. Ask me anything about:

• Kaspa's GHOSTDAG consensus mechanism
• Mining and network details  
• Technical specifications
• Comparisons with other cryptocurrencies
• Development roadmap
• And much more!

What would you like to know about Kaspa?`
    }
  ])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [lastQ, setLastQ] = useState<string>()
  const [lastA, setLastA] = useState<string>()
  const [tweetStatus, setTweetStatus] = useState<string>()
  const [conversationId, setConversationId] = useState<string>()

  const handleSend = async () => {
    if (!input.trim() || loading) return

    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: input.trim()
    }

    setMessages(prev => [...prev, userMessage])
    setLastQ(input.trim())
    setInput('')
    setLoading(true)

    try {
      const response = await ask(input.trim(), conversationId)
      
      // Store conversation ID from response
      if (response.conversation_id && !conversationId) {
        setConversationId(response.conversation_id)
      }
      
      const assistantMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: response.answer,
        citations: response.citations
      }

      setMessages(prev => [...prev, assistantMessage])
      setLastA(response.answer)
    } catch (error) {
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: 'Sorry, I encountered an error while processing your question. Please try again.'
      }
      setMessages(prev => [...prev, errorMessage])
    } finally {
      setLoading(false)
    }
  }

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement | HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  const postToTwitter = async () => {
    if (!lastQ || !lastA) return

    try {
      setTweetStatus('Posting to Twitter...')
      const response = await fetch('http://localhost:8000/post_last_qa_to_twitter', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question: lastQ, answer: lastA })
      })

      if (response.ok) {
        setTweetStatus('Successfully posted to Twitter! 🐦')
      } else {
        throw new Error('Failed to post')
      }
    } catch (error) {
      setTweetStatus('Failed to post to Twitter ❌')
    }

    setTimeout(() => setTweetStatus(''), 5000)
  }
  return (
    <div className="min-h-screen flex flex-col" style={{ backgroundColor: '#0b0f17' }}>
      {/* Enhanced Header */}
      <header className="sticky top-0 z-10 border-b border-kaspa/20 bg-background/80 backdrop-blur">
        <div className="max-w-6xl mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            {/* Logo and Title */}
            <div className="flex items-center gap-4">
              <img 
                src={kaspaLogo} 
                alt="Kaspa Logo" 
                className="w-10 h-10 rounded-full ring-2 ring-kaspa/30 hover:ring-kaspa/60 transition-all"
              />
              <div>
                <h1 className="text-2xl font-bold text-white neon">KaspaBot</h1>
                <p className="text-kaspa/70 text-sm">AI-Powered Kaspa Assistant</p>
              </div>
            </div>
            
            {/* Status Indicator */}
            <div className="flex items-center gap-3">
              <div className="flex items-center gap-2">
                <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse"></div>
                <span className="text-green-400 text-sm font-medium">Online</span>
              </div>
            </div>
          </div>
          
          {/* Knowledge Base Stats */}
          <div className="mt-4 flex items-center justify-center">
            <div className="glass-card px-4 py-2 rounded-full">
              <div className="flex items-center gap-6 text-sm">
                <div className="flex items-center gap-2">
                  <span className="text-kaspa">📚</span>
                  <span className="text-slate-300">369 Knowledge Chunks</span>
                </div>
                <div className="flex items-center gap-2">
                  <span className="text-kaspa">🧠</span>
                  <span className="text-slate-300">Vector Database</span>
                </div>
                <div className="flex items-center gap-2">
                  <span className="text-kaspa">⚡</span>
                  <span className="text-slate-300">Real-time Answers</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="flex-1">
        <div className="max-w-6xl mx-auto px-4 py-6">
          <div className="glass-card rounded-2xl p-6 shadow-2xl">
            <Chat 
              messages={messages}
              input={input}
              setInput={setInput}
              onSend={handleSend}
              loading={loading}
              onKeyDown={handleKeyDown}
              lastQ={lastQ}
              lastA={lastA}
              postToTwitter={postToTwitter}
              tweetStatus={tweetStatus}
            />
          </div>
        </div>
      </main>

      {/* Enhanced Footer */}
      <footer className="border-t border-kaspa/10 py-6">
        <div className="max-w-6xl mx-auto px-4">
          <div className="flex items-center justify-between">
            <div className="text-xs text-slate-400">
              Powered by <span className="text-kaspa font-medium">Kasparchive RAG AI</span>
            </div>
            <div className="flex items-center gap-4 text-xs text-slate-400">
              <a href="https://kasparchive.com" target="_blank" rel="noopener noreferrer" 
                 className="hover:text-kaspa transition-colors">
                📖 Knowledge Base
              </a>
              <a href="https://twitter.com/kasparchive" target="_blank" rel="noopener noreferrer"
                 className="hover:text-kaspa transition-colors">
                🐦 Twitter
              </a>
              <a href="https://github.com/kaspa" target="_blank" rel="noopener noreferrer"
                 className="hover:text-kaspa transition-colors">
                💻 GitHub
              </a>
            </div>
          </div>
        </div>
      </footer>
    </div>
  )
}


