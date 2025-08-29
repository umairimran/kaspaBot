export default function InfoCard({ title, children }) {
  return (
    <div className="card p-4">
      {title && <h3 className="text-sm font-semibold text-slate-300 mb-2">{title}</h3>}
      {children}
    </div>
  )
}
