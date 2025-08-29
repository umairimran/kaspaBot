import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'

export default function Header({ onToggleSidebar }) {
  const [open, setOpen] = useState(false)

  return (
    <header className="sticky top-0 z-30 border-b border-slate-800/60 bg-slate-950/60 backdrop-blur supports-[backdrop-filter]:bg-slate-950/40">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <div className="flex h-16 items-center justify-between">
          <div className="flex items-center gap-3">
            <button className="lg:hidden -ml-1 p-2 rounded-lg hover:bg-slate-800/60" onClick={onToggleSidebar} aria-label="Toggle sidebar">
              <svg className="h-6 w-6 text-slate-200" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" d="M4 6h16M4 12h16M4 18h16" />
              </svg>
            </button>
            <div className="flex items-center gap-2">
              <div className="h-8 w-8 rounded-lg bg-gradient-to-tr from-kaspa-500 via-indigo-500 to-purple-600 p-[2px]">
                <div className="h-full w-full rounded-[6px] bg-slate-950 grid place-items-center">
                  <span className="text-xs font-bold tracking-widest">K</span>
                </div>
              </div>
              <div>
                <h1 className="text-sm font-semibold tracking-wider text-slate-200">KASPA CHATBOT</h1>
                <p className="text-[10px] text-slate-400 -mt-0.5">Crypto-native assistant</p>
              </div>
            </div>
          </div>

          <nav className="hidden md:flex items-center gap-6 text-sm">
            {['Home','Chat','Docs','About'].map(x => (
              <a key={x} href="#" className="text-slate-300 hover:text-white transition">{x}</a>
            ))}
          </nav>

          <div className="flex items-center gap-2">
            <button className="btn-primary text-sm">Launch App</button>
            <button className="md:hidden -mr-1 p-2 rounded-lg hover:bg-slate-800/60" onClick={() => setOpen(v=>!v)} aria-label="Toggle nav">
              <svg className="h-6 w-6 text-slate-200" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" d="M5 12h14M12 5l7 7-7 7" />
              </svg>
            </button>
          </div>
        </div>

        <AnimatePresence>
          {open && (
            <motion.div
              initial={{ height: 0, opacity: 0 }}
              animate={{ height: 'auto', opacity: 1 }}
              exit={{ height: 0, opacity: 0 }}
              className="md:hidden overflow-hidden"
            >
              <div className="py-2 flex flex-col gap-1 text-sm">
                {['Home','Chat','Docs','About'].map(x => (
                  <a key={x} href="#" className="rounded-lg px-3 py-2 text-slate-300 hover:bg-slate-800/60 hover:text-white">{x}</a>
                ))}
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </header>
  )
}
