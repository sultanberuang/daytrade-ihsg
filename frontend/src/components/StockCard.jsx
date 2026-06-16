import { TrendingUp, TrendingDown, Minus, Volume2, Gauge } from 'lucide-react'
import TradePlan from './TradePlan'
import NewsPanel from './NewsPanel'

const actionStyles = {
  BUY: 'badge-buy',
  SELL: 'badge-sell',
  HOLD: 'badge-hold',
}

const actionIcons = {
  BUY: TrendingUp,
  SELL: TrendingDown,
  HOLD: Minus,
}

function ScoreRing({ score }) {
  const color =
    score >= 70 ? '#00d4aa' : score <= 35 ? '#ff4757' : '#ffa502'
  const circumference = 2 * Math.PI * 36
  const offset = circumference - (score / 100) * circumference

  return (
    <div className="relative w-20 h-20 shrink-0">
      <svg className="w-20 h-20 -rotate-90" viewBox="0 0 80 80">
        <circle cx="40" cy="40" r="36" fill="none" stroke="#243044" strokeWidth="6" />
        <circle
          cx="40"
          cy="40"
          r="36"
          fill="none"
          stroke={color}
          strokeWidth="6"
          strokeLinecap="round"
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          className="transition-all duration-700"
        />
      </svg>
      <div className="absolute inset-0 flex items-center justify-center">
        <span className="text-lg font-bold font-mono" style={{ color }}>{score}</span>
      </div>
    </div>
  )
}

export default function StockCard({ stock, featured = false }) {
  const ActionIcon = actionIcons[stock.action]
  const isPositive = stock.change_pct >= 0

  return (
    <div
      className={`rounded-2xl border border-gray-800 bg-surface-card p-5 hover:border-gray-700 transition-all ${
        featured ? 'md:max-w-2xl' : ''
      }`}
    >
      <div className="flex items-start justify-between gap-3 mb-4">
        <div className="min-w-0">
          <div className="flex items-center gap-2 mb-1">
            <span className="font-mono font-bold text-white">{stock.code || stock.ticker}</span>
            <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-md text-xs font-semibold ${actionStyles[stock.action]}`}>
              <ActionIcon className="w-3 h-3" />
              {stock.action}
            </span>
          </div>
          <p className="text-sm text-gray-500 truncate">{stock.name}</p>
        </div>
        <ScoreRing score={stock.score} />
      </div>

      <div className="flex items-baseline gap-3 mb-4">
        <span className="text-2xl font-bold font-mono">
          {stock.currency === 'IDR'
            ? `Rp ${stock.price.toLocaleString('id-ID')}`
            : `$${stock.price.toLocaleString('en-US', { minimumFractionDigits: 2 })}`}
        </span>
        <span className={`text-sm font-mono font-medium ${isPositive ? 'text-emerald-400' : 'text-red-400'}`}>
          {isPositive ? '+' : ''}{stock.change_pct}%
        </span>
      </div>

      <div className="grid grid-cols-3 gap-3 mb-4">
        <div className="p-2 rounded-lg bg-surface-hover/50">
          <div className="flex items-center gap-1 text-xs text-gray-500 mb-1">
            <Gauge className="w-3 h-3" /> RSI
          </div>
          <span className="font-mono text-sm font-medium">
            {stock.rsi ?? '—'}
          </span>
        </div>
        <div className="p-2 rounded-lg bg-surface-hover/50">
          <div className="flex items-center gap-1 text-xs text-gray-500 mb-1">
            <Volume2 className="w-3 h-3" /> Rel Vol
          </div>
          <span className="font-mono text-sm font-medium">
            {stock.rel_volume ? `${stock.rel_volume}x` : '—'}
          </span>
        </div>
        <div className="p-2 rounded-lg bg-surface-hover/50">
          <div className="text-xs text-gray-500 mb-1">ATR %</div>
          <span className="font-mono text-sm font-medium">
            {stock.atr_pct ? `${stock.atr_pct}%` : '—'}
          </span>
        </div>
      </div>

      {stock.trade_plan && (
        <div className="mb-4">
          <TradePlan plan={stock.trade_plan} currency={stock.currency} />
        </div>
      )}

      {stock.news && (
        <div className="mb-4">
          <NewsPanel news={stock.news} />
        </div>
      )}

      {stock.signals?.length > 0 && (
        <div className="flex flex-wrap gap-1.5 mb-3">
          {stock.signals.map((sig, i) => (
            <span
              key={i}
              className={`text-xs px-2 py-1 rounded-md ${
                sig.type === 'bullish'
                  ? 'bg-emerald-500/10 text-emerald-400'
                  : sig.type === 'bearish'
                  ? 'bg-red-500/10 text-red-400'
                  : 'bg-gray-500/10 text-gray-400'
              }`}
            >
              {sig.name}
            </span>
          ))}
        </div>
      )}

      {stock.reasons?.length > 0 && (
        <div className="border-t border-gray-800 pt-3 space-y-1">
          {stock.reasons.map((r, i) => (
            <p key={i} className="text-xs text-gray-500 font-mono">{r}</p>
          ))}
        </div>
      )}
    </div>
  )
}
