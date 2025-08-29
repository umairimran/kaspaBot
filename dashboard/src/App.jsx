import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import Header from './components/Header.jsx'
import Sidebar from './components/Sidebar.jsx'
import ChatWindow from './components/ChatWindow.jsx'
import InfoCard from './components/InfoCard.jsx'
import Ticker from './components/Ticker.jsx'
import StatusPill from './components/StatusPill.jsx'
import { useChat } from './hooks/useChat.js'
import { useKaspaStats } from './hooks/useKaspaStats.js'

export default function App() {
  const [sidebarOpen, setSidebarOpen] = useState(false)
  const { messages, sendMessage, conversations, setActiveConversation } = useChat()
  const { price, change24h } = useKaspaStats()

  return (
    <div className="min-h-screen bg-[radial-gradient(1200px_600px_at_10%_10%,rgba(0,163,255,0.10),rgba(0,0,0,0)),radial-gradient(800px_400px_at_90%_10%,rgba(147,51,234,0.08),rgba(0,0,0,0))]">
      <Header onToggleSidebar={() => setSidebarOpen(v => !v)} />

      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-4 py-4">
          {/* Sidebar */}
          <div className="lg:col-span-3">
            <div className="hidden lg:block sticky top-4">
              <Sidebar open={true} conversations={conversations} onSelect={setActiveConversation} />
            </div>
            <AnimatePresence>
              {sidebarOpen && (
                <motion.div
                  className="fixed inset-0 z-40 lg:hidden"
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  exit={{ opacity: 0 }}
                >
                  <div className="absolute inset-0 bg-black/50" onClick={() => setSidebarOpen(false)} />
                  <motion.div
                    className="absolute left-0 top-0 h-full w-80 p-4"
                    initial={{ x: -320 }}
                    animate={{ x: 0 }}
                    exit={{ x: -320 }}
                    transition={{ type: 'spring', stiffness: 260, damping: 24 }}
                  >
                    <Sidebar open={true} conversations={conversations} onSelect={(id) => { setActiveConversation(id); setSidebarOpen(false) }} />
                  </motion.div>
                </motion.div>
              )}
            </AnimatePresence>
          </div>

          {/* Chat */}
          <div className="lg:col-span-6 order-first lg:order-none">
            <ChatWindow messages={messages} onSend={sendMessage} />
          </div>

          {/* Info widgets */}
          <div className="lg:col-span-3 space-y-4">
            <Ticker symbol="KAS" price={price} change24h={change24h} />

            <InfoCard title="Kaspa Resources">
              <ul className="space-y-2 text-sm">
                <li><a className="text-kaspa-400 hover:text-kaspa-300 underline underline-offset-4" href="#">Official Website</a></li>
                <li><a className="text-kaspa-400 hover:text-kaspa-300 underline underline-offset-4" href="#">Docs</a></li>
                <li><a className="text-kaspa-400 hover:text-kaspa-300 underline underline-offset-4" href="#">Discord</a></li>
              </ul>
            </InfoCard>

            <InfoCard title="System Status">
              <div className="space-y-2">
                <StatusPill status="connected" label="Knowledge Base" />
                <StatusPill status="healthy" label="Vector DB" />
                <StatusPill status="syncing" label="Indexer" />
              </div>
            </InfoCard>

          </div>
        </div>
      </div>
    </div>
  )
}
