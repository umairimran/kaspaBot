export default function Ticker({ symbol = 'KAS', price = 0.0, change24h = 0.0 }) {
  const up = change24h >= 0
  return (
    <div className="card p-4">
      <div className="flex items-center justify-between">
        <div>
          <div className="text-xs text-slate-500">Kaspa</div>
          <div className="flex items-end gap-2">
            <div className="text-2xl font-mono font-semibold tracking-tight">${price.toFixed(4)}</div>
            <div className={`text-xs px-2 py-0.5 rounded-md ${up ? 'bg-emerald-500/15 text-emerald-400' : 'bg-rose-500/15 text-rose-400'}`}>{up ? '+' : ''}{change24h.toFixed(2)}%</div>
          </div>
        </div>
        <div className="h-12 w-12 rounded-xl bg-gradient-to-tr from-kaspa-500 via-indigo-500 to-purple-600 p-[2px]">
          <div className="h-full w-full rounded-[10px] bg-slate-950 grid place-items-center text-xs font-bold">{symbol}</div>
        </div>
      </div>
      <div className="mt-3 text-[10px] text-slate-500">Streaming data placeholder</div>
    </div>
  )
}
