import { Target, ShieldAlert, TrendingUp } from 'lucide-react'

function formatPrice(price, currency = 'IDR') {
  if (price == null) return '—'
  if (currency === 'IDR') return `Rp ${price.toLocaleString('id-ID')}`
  return `$${price.toLocaleString('en-US', { minimumFractionDigits: 2 })}`
}

export default function TradePlan({ plan, currency = 'IDR', compact = false }) {
  if (!plan) return null

  const { entry, sl, tp1, tp2, risk_reward, risk_pct, reward_pct, note } = plan

  if (compact) {
    return (
      <div className="font-mono text-xs space-y-0.5">
        <div className="text-blue-400">E: {formatPrice(entry, currency)}</div>
        <div className="text-red-400">SL: {formatPrice(sl, currency)}</div>
        <div className="text-emerald-400">TP: {formatPrice(tp1, currency)}</div>
      </div>
    )
  }

  return (
    <div className="rounded-xl border border-gray-800 bg-surface-hover/30 p-4 space-y-3">
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-semibold text-gray-300 flex items-center gap-2">
          <Target className="w-4 h-4 text-accent-green" />
          Rencana Trading
        </h3>
        {risk_reward && (
          <span className="text-xs font-mono px-2 py-1 rounded-md bg-accent-green/10 text-accent-green">
            R:R 1:{risk_reward}
          </span>
        )}
      </div>

      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        <div className="p-3 rounded-lg bg-blue-500/5 border border-blue-500/20">
          <p className="text-xs text-blue-400 mb-1">Entry</p>
          <p className="font-mono font-bold text-white">{formatPrice(entry, currency)}</p>
        </div>
        <div className="p-3 rounded-lg bg-red-500/5 border border-red-500/20">
          <p className="text-xs text-red-400 mb-1 flex items-center gap-1">
            <ShieldAlert className="w-3 h-3" /> Stop Loss
          </p>
          <p className="font-mono font-bold text-white">{formatPrice(sl, currency)}</p>
          {risk_pct != null && (
            <p className="text-xs text-red-400/70 mt-0.5">-{risk_pct}%</p>
          )}
        </div>
        <div className="p-3 rounded-lg bg-emerald-500/5 border border-emerald-500/20">
          <p className="text-xs text-emerald-400 mb-1 flex items-center gap-1">
            <TrendingUp className="w-3 h-3" /> TP1
          </p>
          <p className="font-mono font-bold text-white">{formatPrice(tp1, currency)}</p>
          {reward_pct != null && (
            <p className="text-xs text-emerald-400/70 mt-0.5">+{reward_pct}%</p>
          )}
        </div>
        <div className="p-3 rounded-lg bg-emerald-500/5 border border-emerald-500/10">
          <p className="text-xs text-emerald-400/70 mb-1">TP2</p>
          <p className="font-mono font-bold text-gray-300">{formatPrice(tp2, currency)}</p>
        </div>
      </div>

      {note && (
        <p className="text-xs text-gray-500">{note}</p>
      )}
    </div>
  )
}

export { formatPrice }
