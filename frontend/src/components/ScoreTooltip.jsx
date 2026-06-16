import { Info } from 'lucide-react'

const METHODOLOGY = {
  buy: [
    'Skor ≥ 75',
    'Min. 2 sinyal bullish',
    'Konfirmasi tren (MACD / EMA / Volume)',
    'Likuiditas ≥ Rp 5M/hari',
  ],
  weights: [
    'Basis: 50 poin',
    'Sinyal bullish: +6',
    'Sinyal bearish: -6',
    'Momentum ±5 (chg > 2%)',
    'Volatilitas +5 (ATR > 3%)',
    'Berita: ±5 s/d ±10',
  ],
}

export function ScoreTooltipHeader({ breakdown }) {
  return (
    <div className="relative group inline-flex items-center gap-1">
      <span>Skor</span>
      <Info className="w-3.5 h-3.5 opacity-50 group-hover:opacity-100" />
      <div className="invisible group-hover:visible opacity-0 group-hover:opacity-100 transition-all absolute z-50 top-full left-1/2 -translate-x-1/2 mt-2 w-72 p-3 rounded-xl bg-gray-900 border border-gray-700 shadow-xl text-left pointer-events-none">
        <p className="text-xs font-semibold text-white mb-2">Metodologi Skor</p>
        <ul className="text-xs text-gray-400 space-y-1 mb-2">
          {METHODOLOGY.weights.map((w) => (
            <li key={w}>• {w}</li>
          ))}
        </ul>
        <p className="text-xs font-semibold text-emerald-400 mb-1">Syarat BUY:</p>
        <ul className="text-xs text-gray-400 space-y-1">
          {METHODOLOGY.buy.map((b) => (
            <li key={b}>• {b}</li>
          ))}
        </ul>
        {breakdown && (
          <p className="text-xs text-gray-500 mt-2 border-t border-gray-800 pt-2">
            Klik baris untuk detail breakdown per saham.
          </p>
        )}
      </div>
    </div>
  )
}

export function ScoreBreakdown({ breakdown }) {
  if (!breakdown?.items) return null
  return (
    <div className="rounded-xl border border-gray-800 bg-surface-hover/30 p-4 space-y-2">
      <p className="text-sm font-semibold text-gray-300">Breakdown Skor ({breakdown.total})</p>
      <div className="space-y-1">
        {breakdown.items.map((item, i) => (
          <div key={i} className="flex justify-between text-xs font-mono">
            <span className="text-gray-500">{item.label}</span>
            <span className={
              item.value > 0 ? 'text-emerald-400' : item.value < 0 ? 'text-red-400' : 'text-gray-400'
            }>
              {item.value > 0 ? '+' : ''}{item.value}
            </span>
          </div>
        ))}
      </div>
    </div>
  )
}
