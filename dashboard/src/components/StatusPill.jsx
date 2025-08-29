const variants = {
  connected: 'bg-emerald-500/15 text-emerald-400 border-emerald-500/20',
  healthy: 'bg-sky-500/15 text-sky-400 border-sky-500/20',
  syncing: 'bg-amber-500/15 text-amber-400 border-amber-500/20',
  down: 'bg-rose-500/15 text-rose-400 border-rose-500/20',
}

export default function StatusPill({ status = 'connected', label = '' }) {
  return (
    <div className={`inline-flex items-center gap-2 rounded-lg border px-2.5 py-1 text-xs ${variants[status] || variants.connected}`}>
      <span className={`h-1.5 w-1.5 rounded-full ${status === 'down' ? 'bg-rose-400' : 'bg-emerald-400'} animate-pulse`} />
      <span className="text-slate-300/90">{label}</span>
      <span className="text-slate-500">•</span>
      <span className="capitalize">{status}</span>
    </div>
  )
}
