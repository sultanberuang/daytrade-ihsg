import { TrendingUp, TrendingDown, Minus, ChevronUp, ChevronDown, ChevronsUpDown } from 'lucide-react'
import { formatPrice } from './TradePlan'

const actionStyles = {
  BUY: 'text-emerald-400 bg-emerald-500/10',
  SELL: 'text-red-400 bg-red-500/10',
  HOLD: 'text-amber-400 bg-amber-500/10',
}

const actionIcons = {
  BUY: TrendingUp,
  SELL: TrendingDown,
  HOLD: Minus,
}

const COLUMNS = [
  { key: 'code', label: 'Kode', align: 'left', sortable: true },
  { key: 'name', label: 'Nama Emiten', align: 'left', sortable: true, className: 'hidden md:table-cell' },
  { key: 'price', label: 'Harga', align: 'right', sortable: true },
  { key: 'change_pct', label: 'Chg%', align: 'right', sortable: true },
  { key: 'rsi', label: 'RSI', align: 'right', sortable: true, className: 'hidden sm:table-cell' },
  { key: 'volume', label: 'Vol', align: 'right', sortable: true, className: 'hidden lg:table-cell' },
  { key: 'entry', label: 'Entry', align: 'right', sortable: false, className: 'hidden xl:table-cell' },
  { key: 'sl', label: 'SL', align: 'right', sortable: false, className: 'hidden xl:table-cell' },
  { key: 'tp1', label: 'TP1', align: 'right', sortable: false, className: 'hidden xl:table-cell' },
  { key: 'news_sentiment', label: 'Berita', align: 'center', sortable: true, className: 'hidden lg:table-cell' },
  { key: 'score', label: 'Skor', align: 'center', sortable: true },
  { key: 'action', label: 'Sinyal', align: 'center', sortable: true },
]

function formatVolume(vol) {
  if (vol >= 1_000_000) return `${(vol / 1_000_000).toFixed(1)}M`
  if (vol >= 1_000) return `${(vol / 1_000).toFixed(0)}K`
  return vol.toLocaleString('id-ID')
}

function SortIcon({ column, sortField, sortOrder }) {
  if (column !== sortField) {
    return <ChevronsUpDown className="w-3 h-3 opacity-30" />
  }
  return sortOrder === 'asc'
    ? <ChevronUp className="w-3 h-3 text-accent-green" />
    : <ChevronDown className="w-3 h-3 text-accent-green" />
}

function NewsBadge({ label, score }) {
  const styles = {
    bullish: 'text-emerald-400 bg-emerald-500/10',
    bearish: 'text-red-400 bg-red-500/10',
    neutral: 'text-gray-400 bg-gray-500/10',
  }
  return (
    <span className={`text-xs px-1.5 py-0.5 rounded-md font-medium ${styles[label] || styles.neutral}`}>
      {label === 'bullish' ? '↑' : label === 'bearish' ? '↓' : '—'}
      {score !== 0 && ` ${score > 0 ? '+' : ''}${score}`}
    </span>
  )
}

function SortableHeader({ col, sortField, sortOrder, onSort }) {
  const align = col.align === 'right' ? 'text-right' : col.align === 'center' ? 'text-center' : 'text-left'
  const base = `px-4 py-3 font-medium ${align} ${col.className || ''}`

  if (!col.sortable) {
    return <th className={base}>{col.label}</th>
  }

  return (
    <th className={base}>
      <button
        type="button"
        onClick={() => onSort(col.key)}
        className={`inline-flex items-center gap-1 hover:text-gray-200 transition-colors ${
          col.align === 'right' ? 'flex-row-reverse ml-auto' : col.align === 'center' ? 'mx-auto' : ''
        } ${sortField === col.key ? 'text-accent-green' : ''}`}
      >
        {col.label}
        <SortIcon column={col.key} sortField={sortField} sortOrder={sortOrder} />
      </button>
    </th>
  )
}

export default function StockTable({ stocks, onSelect, sortField, sortOrder, onSort }) {
  return (
    <div className="overflow-x-auto rounded-xl border border-gray-800">
      <table className="w-full text-sm">
        <thead>
          <tr className="bg-surface-card text-gray-500 text-left">
            <th className="px-4 py-3 font-medium w-10">#</th>
            {COLUMNS.map((col) => (
              <SortableHeader
                key={col.key}
                col={col}
                sortField={sortField}
                sortOrder={sortOrder}
                onSort={onSort}
              />
            ))}
          </tr>
        </thead>
        <tbody>
          {stocks.map((stock, idx) => {
            const Icon = actionIcons[stock.action]
            const isPositive = stock.change_pct >= 0
            return (
              <tr
                key={stock.ticker}
                onClick={() => onSelect?.(stock)}
                className="border-t border-gray-800/50 hover:bg-surface-hover/50 cursor-pointer transition-colors"
              >
                <td className="px-4 py-3 text-gray-600 font-mono text-xs">{idx + 1}</td>
                <td className="px-4 py-3">
                  <span className="font-mono font-bold text-white">{stock.code || stock.ticker.replace('.JK', '')}</span>
                </td>
                <td className="px-4 py-3 text-gray-400 hidden md:table-cell max-w-[200px] truncate">
                  {stock.name}
                </td>
                <td className="px-4 py-3 text-right font-mono whitespace-nowrap">
                  {formatPrice(stock.price, stock.currency)}
                </td>
                <td className={`px-4 py-3 text-right font-mono font-medium ${isPositive ? 'text-emerald-400' : 'text-red-400'}`}>
                  {isPositive ? '+' : ''}{stock.change_pct}%
                </td>
                <td className="px-4 py-3 text-right font-mono hidden sm:table-cell text-gray-300">
                  {stock.rsi ?? '—'}
                </td>
                <td className="px-4 py-3 text-right font-mono hidden lg:table-cell text-gray-400">
                  {formatVolume(stock.volume)}
                </td>
                <td className="px-4 py-3 text-right font-mono hidden xl:table-cell text-blue-400 whitespace-nowrap">
                  {stock.trade_plan ? formatPrice(stock.trade_plan.entry, stock.currency) : '—'}
                </td>
                <td className="px-4 py-3 text-right font-mono hidden xl:table-cell text-red-400 whitespace-nowrap">
                  {stock.trade_plan ? formatPrice(stock.trade_plan.sl, stock.currency) : '—'}
                </td>
                <td className="px-4 py-3 text-right font-mono hidden xl:table-cell text-emerald-400 whitespace-nowrap">
                  {stock.trade_plan ? formatPrice(stock.trade_plan.tp1, stock.currency) : '—'}
                </td>
                <td className="px-4 py-3 text-center hidden lg:table-cell">
                  <NewsBadge label={stock.news_label || 'neutral'} score={stock.news_sentiment ?? 0} />
                </td>
                <td className="px-4 py-3 text-center">
                  <span className={`inline-block font-mono font-bold text-xs px-2 py-1 rounded-md ${
                    stock.score >= 70 ? 'text-emerald-400' : stock.score <= 35 ? 'text-red-400' : 'text-amber-400'
                  }`}>
                    {stock.score}
                  </span>
                </td>
                <td className="px-4 py-3 text-center">
                  <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-md text-xs font-semibold ${actionStyles[stock.action]}`}>
                    <Icon className="w-3 h-3" />
                    {stock.action}
                  </span>
                </td>
              </tr>
            )
          })}
        </tbody>
      </table>
    </div>
  )
}

export { COLUMNS }
