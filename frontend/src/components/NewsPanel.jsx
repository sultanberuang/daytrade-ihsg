import { Newspaper, ExternalLink } from 'lucide-react'

const labelStyles = {
  bullish: 'text-emerald-400 bg-emerald-500/10 border-emerald-500/20',
  bearish: 'text-red-400 bg-red-500/10 border-red-500/20',
  neutral: 'text-gray-400 bg-gray-500/10 border-gray-500/20',
}

export default function NewsPanel({ news }) {
  if (!news?.headlines?.length) {
    return (
      <div className="rounded-xl border border-gray-800 bg-surface-hover/30 p-4">
        <p className="text-xs text-gray-500">Tidak ada berita terbaru untuk saham ini.</p>
      </div>
    )
  }

  const { sentiment, headlines } = news
  const label = sentiment?.label || 'neutral'

  return (
    <div className="rounded-xl border border-gray-800 bg-surface-hover/30 p-4 space-y-3">
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-semibold text-gray-300 flex items-center gap-2">
          <Newspaper className="w-4 h-4 text-blue-400" />
          Analisis Berita
        </h3>
        <span className={`text-xs px-2 py-1 rounded-md border font-medium capitalize ${labelStyles[label]}`}>
          {label} ({sentiment?.score > 0 ? '+' : ''}{sentiment?.score ?? 0})
        </span>
      </div>

      <ul className="space-y-2">
        {headlines.map((item, i) => (
          <li key={i} className="text-xs">
            {item.link ? (
              <a
                href={item.link}
                target="_blank"
                rel="noopener noreferrer"
                className="text-gray-400 hover:text-gray-200 flex items-start gap-2 group"
                onClick={(e) => e.stopPropagation()}
              >
                <ExternalLink className="w-3 h-3 shrink-0 mt-0.5 opacity-50 group-hover:opacity-100" />
                <span className="line-clamp-2">{item.title}</span>
              </a>
            ) : (
              <span className="text-gray-400 line-clamp-2">{item.title}</span>
            )}
            {item.source && (
              <span className="text-gray-600 ml-5">{item.source}</span>
            )}
          </li>
        ))}
      </ul>
    </div>
  )
}
