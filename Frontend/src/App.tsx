import Chat from './components/Chat'

export default function App() {
  return (
    <div className="min-h-screen flex flex-col" style={{ backgroundColor: '#0b0f17' }}>
      <header className="sticky top-0 z-10 border-b border-kaspa/20 bg-background/80 backdrop-blur">
        <div className="max-w-5xl mx-auto px-4 py-4 flex items-center justify-between">
          <div className="text-xl font-bold text-white neon">KaspaBot</div>
          <div className="text-kaspa text-sm">kasparchive.com</div>
        </div>
      </header>
      <main className="flex-1">
        <div className="max-w-5xl mx-auto px-4 py-6">
          <div className="glass-card rounded-2xl p-4">
            <Chat />
          </div>
        </div>
      </main>
      <footer className="border-t border-kaspa/10 py-4 text-center text-xs text-slate-400">
        Powered by Kasparchive RAG AI
      </footer>
    </div>
  )
}


