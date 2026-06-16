import { TrendingUp, TrendingDown, Minus, Layers } from 'lucide-react'

export default function StatsBar({ buy, sell, hold, total }) {
  const stats = [
    { label: 'Total Scan', value: total, icon: Layers, color: 'text-blue-400' },
    { label: 'Buy Signal', value: buy, icon: TrendingUp, color: 'text-emerald-400' },
    { label: 'Hold', value: hold, icon: Minus, color: 'text-amber-400' },
    { label: 'Sell Signal', value: sell, icon: TrendingDown, color: 'text-red-400' },
  ]

  return (
    <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
      {stats.map(({ label, value, icon: Icon, color }) => (
        <div
          key={label}
          className="flex items-center gap-3 p-4 rounded-xl bg-surface-card border border-gray-800"
        >
          <div className={`p-2 rounded-lg bg-surface-hover ${color}`}>
            <Icon className="w-5 h-5" />
          </div>
          <div>
            <p className="text-2xl font-bold font-mono">{value}</p>
            <p className="text-xs text-gray-500">{label}</p>
          </div>
        </div>
      ))}
    </div>
  )
}
