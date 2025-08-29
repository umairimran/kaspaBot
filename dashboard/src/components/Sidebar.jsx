import { motion } from 'framer-motion'

export default function Sidebar({ open = true, conversations = [], onSelect }) {
  return (
    <motion.aside
      className="card h-[70vh] lg:h-[calc(100vh-6rem)] p-3"
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
    >
      <div className="flex items-center justify-between px-2 pb-2">
        <h2 className="text-sm font-semibold text-slate-300">Conversations</h2>
        <button className="text-xs text-kaspa-400 hover:text-kaspa-300">New</button>
      </div>
      <div className="space-y-2 overflow-auto pr-1 h-full">
        {conversations.map((c) => (
          <button
            key={c.id}
            onClick={() => onSelect?.(c.id)}
            className="w-full text-left rounded-lg border border-slate-800/80 bg-slate-900/60 px-3 py-2 hover:border-kaspa-500/40"
          >
            <div className="flex items-center justify-between">
              <span className="text-sm text-slate-200">{c.title}</span>
              <span className="text-[10px] text-slate-500">{c.updatedAt}</span>
            </div>
            <div className="text-xs text-slate-400 truncate">{c.preview}</div>
          </button>
        ))}
        {conversations.length === 0 && (
          <div className="text-xs text-slate-500 px-2">No conversations yet.</div>
        )}
      </div>
    </motion.aside>
  )
}
