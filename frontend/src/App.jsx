import { useState, useEffect, useCallback, useRef } from 'react'
import {
  TrendingUp,
  TrendingDown,
  RefreshCw,
  Search,
  Activity,
  BarChart3,
  Zap,
  AlertTriangle,
  ChevronLeft,
  ChevronRight,
} from 'lucide-react'
import StockTable from './components/StockTable'
import StockCard from './components/StockCard'
import StatsBar from './components/StatsBar'

const API = import.meta.env.VITE_API_URL || '/api'
const POLL_INTERVAL = 3000
const TEXT_SORT_FIELDS = new Set(['code', 'name'])

export default function App() {
  const [stocks, setStocks] = useState([])
  const [summary, setSummary] = useState({ buy: 0, sell: 0, hold: 0, analyzed: 0 })
  const [totalListed, setTotalListed] = useState(955)
  const [loading, setLoading] = useState(true)
  const [scanning, setScanning] = useState(false)
  const [scanProgress, setScanProgress] = useState({ progress: 0, total: 0 })
  const [error, setError] = useState(null)
  const [searchTicker, setSearchTicker] = useState('')
  const [searchQuery, setSearchQuery] = useState('')
  const [searchResult, setSearchResult] = useState(null)
  const [filter, setFilter] = useState('ALL')
  const [liquidOnly, setLiquidOnly] = useState(false)
  const [sortField, setSortField] = useState('score')
  const [sortOrder, setSortOrder] = useState('desc')
  const [page, setPage] = useState(1)
  const [pages, setPages] = useState(1)
  const [totalCount, setTotalCount] = useState(0)
  const [lastUpdated, setLastUpdated] = useState(null)
  const pollRef = useRef(null)

  const fetchScan = useCallback(async (pageNum = page, forceRefresh = false) => {
    setError(null)
    try {
      const params = new URLSearchParams({
        page: String(pageNum),
        limit: '50',
        sort: sortField,
        order: sortOrder,
      })
      if (filter !== 'ALL') params.set('action', filter)
      if (searchQuery) params.set('q', searchQuery)
      if (liquidOnly) params.set('liquid_only', 'true')
      if (forceRefresh) params.set('refresh', 'true')

      const res = await fetch(`${API}/scan?${params}`)
      if (!res.ok) throw new Error('Gagal memuat data')
      const data = await res.json()

      setStocks(data.recommendations)
      setSummary(data.summary || { buy: 0, sell: 0, hold: 0, analyzed: 0 })
      setTotalListed(data.total_listed || 955)
      setPages(data.pages || 1)
      setTotalCount(data.count || 0)
      setPage(data.page || 1)

      const scan = data.scan || {}
      setScanning(scan.status === 'scanning')
      setScanProgress({ progress: scan.progress || 0, total: scan.total || totalListed })
      if (scan.updated_at) setLastUpdated(new Date(scan.updated_at))

      setLoading(false)
      return scan.status
    } catch (e) {
      setError(e.message)
      setLoading(false)
      return 'error'
    }
  }, [page, filter, sortField, sortOrder, searchQuery, liquidOnly, totalListed])

  const handleSort = (field) => {
    if (field === sortField) {
      setSortOrder((prev) => (prev === 'desc' ? 'asc' : 'desc'))
    } else {
      setSortField(field)
      setSortOrder(TEXT_SORT_FIELDS.has(field) ? 'asc' : 'desc')
    }
    setPage(1)
  }

  useEffect(() => {
    setPage(1)
    setLoading(true)
    fetchScan(1)
  }, [filter, sortField, sortOrder, searchQuery, liquidOnly]) // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    if (scanning) {
      pollRef.current = setInterval(() => fetchScan(page), POLL_INTERVAL)
    }
    return () => clearInterval(pollRef.current)
  }, [scanning, page, fetchScan])

  const handleRefresh = () => {
    setLoading(true)
    setSearchResult(null)
    fetchScan(1, true)
  }

  const handleSearch = async (e) => {
    e.preventDefault()
    const q = searchTicker.trim()
    if (!q) {
      setSearchQuery('')
      setSearchResult(null)
      return
    }

    if (q.length <= 5 && !q.includes(' ')) {
      setLoading(true)
      setError(null)
      try {
        const res = await fetch(`${API}/analyze/${q}`)
        if (!res.ok) throw new Error(`Saham ${q} tidak ditemukan`)
        setSearchResult(await res.json())
        setLoading(false)
        return
      } catch {
        setSearchQuery(q)
        setSearchResult(null)
        setPage(1)
        setLoading(true)
        fetchScan(1)
        return
      }
    }

    setSearchQuery(q)
    setSearchResult(null)
    setPage(1)
  }

  const handlePageChange = (newPage) => {
    setPage(newPage)
    setLoading(true)
    fetchScan(newPage)
  }

  const progressPct = scanProgress.total
    ? Math.round((scanProgress.progress / scanProgress.total) * 100)
    : 0

  return (
    <div className="min-h-screen">
      <header className="border-b border-gray-800 bg-surface-card/80 backdrop-blur-sm sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 py-4 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-xl bg-accent-green/10">
              <Zap className="w-6 h-6 text-accent-green" />
            </div>
            <div>
              <h1 className="text-xl font-bold tracking-tight">DayTrade Pro</h1>
              <p className="text-xs text-gray-500">
                IHSG — {totalListed} saham terdaftar
              </p>
            </div>
          </div>

          <button
            onClick={handleRefresh}
            disabled={scanning}
            className="flex items-center gap-2 px-4 py-2 rounded-lg bg-accent-blue/20 text-blue-400 border border-accent-blue/30 hover:bg-accent-blue/30 transition-all disabled:opacity-50"
          >
            <RefreshCw className={`w-4 h-4 ${scanning ? 'animate-spin' : ''}`} />
            {scanning ? `Scanning ${progressPct}%` : 'Refresh Scan'}
          </button>
        </div>

        {scanning && (
          <div className="max-w-7xl mx-auto px-4 pb-3">
            <div className="h-1.5 bg-gray-800 rounded-full overflow-hidden">
              <div
                className="h-full bg-accent-green transition-all duration-500 rounded-full"
                style={{ width: `${progressPct}%` }}
              />
            </div>
            <p className="text-xs text-gray-500 mt-1">
              Menganalisis {scanProgress.progress}/{scanProgress.total} saham IHSG...
            </p>
          </div>
        )}
      </header>

      <main className="max-w-7xl mx-auto px-4 py-6 space-y-6">
        <div className="flex items-start gap-3 p-4 rounded-xl bg-amber-500/5 border border-amber-500/20">
          <AlertTriangle className="w-5 h-5 text-amber-400 shrink-0 mt-0.5" />
          <p className="text-sm text-gray-400">
            <span className="text-amber-400 font-medium">Disclaimer:</span> Aplikasi ini hanya
            untuk edukasi. Bukan saran investasi. Day trading berisiko tinggi.
          </p>
        </div>

        <form onSubmit={handleSearch} className="flex gap-2">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-500" />
            <input
              type="text"
              value={searchTicker}
              onChange={(e) => setSearchTicker(e.target.value)}
              placeholder="Cari saham IHSG (contoh: BBCA, Bank Central Asia)"
              className="w-full pl-10 pr-4 py-3 rounded-xl bg-surface-card border border-gray-800 focus:border-accent-green/50 focus:outline-none text-sm font-mono"
            />
          </div>
          <button
            type="submit"
            disabled={loading && !searchResult}
            className="px-6 py-3 rounded-xl bg-accent-green/20 text-accent-green border border-accent-green/30 hover:bg-accent-green/30 transition-all font-medium text-sm disabled:opacity-50"
          >
            Cari
          </button>
        </form>

        {!searchResult && summary.analyzed > 0 && (
          <StatsBar
            buy={summary.buy}
            sell={summary.sell}
            hold={summary.hold}
            total={summary.analyzed}
          />
        )}

        {!searchResult && (
          <div className="flex flex-wrap gap-2 items-center justify-between">
            <div className="flex gap-2 flex-wrap">
              {[
                { key: 'ALL', label: 'Semua', icon: BarChart3 },
                { key: 'BUY', label: 'Buy', icon: TrendingUp },
                { key: 'SELL', label: 'Sell', icon: TrendingDown },
                { key: 'HOLD', label: 'Hold', icon: Activity },
              ].map(({ key, label, icon: Icon }) => (
                <button
                  key={key}
                  onClick={() => { setFilter(key); setPage(1) }}
                  className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm transition-all ${
                    filter === key
                      ? 'bg-surface-hover text-white border border-gray-600'
                      : 'text-gray-500 hover:text-gray-300'
                  }`}
                >
                  <Icon className="w-4 h-4" />
                  {label}
                </button>
              ))}
            </div>
            <label className="flex items-center gap-2 text-sm text-gray-400 cursor-pointer">
              <input
                type="checkbox"
                checked={liquidOnly}
                onChange={(e) => { setLiquidOnly(e.target.checked); setPage(1) }}
                className="rounded border-gray-600 bg-surface-card text-accent-green focus:ring-accent-green"
              />
              Hanya likuid (≥ Rp 5M/hari)
            </label>
          </div>
        )}

        {error && (
          <div className="p-4 rounded-xl bg-red-500/10 border border-red-500/20 text-red-400 text-sm">
            {error}
          </div>
        )}

        {loading && !searchResult && stocks.length === 0 && (
          <div className="flex flex-col items-center justify-center py-20 gap-4">
            <RefreshCw className="w-8 h-8 text-accent-green animate-spin" />
            <p className="text-gray-500 text-sm">
              {scanning
                ? `Menganalisis saham IHSG (${scanProgress.progress}/${scanProgress.total})...`
                : 'Memuat data...'}
            </p>
          </div>
        )}

        {searchResult && (
          <div>
            <button
              onClick={() => { setSearchResult(null); fetchScan(page) }}
              className="text-sm text-gray-500 hover:text-gray-300 mb-4"
            >
              ← Kembali ke daftar IHSG
            </button>
            <StockCard stock={searchResult} featured />
          </div>
        )}

        {!searchResult && stocks.length > 0 && (
          <>
            <StockTable
              stocks={stocks}
              onSelect={(s) => setSearchResult(s)}
              sortField={sortField}
              sortOrder={sortOrder}
              onSort={handleSort}
            />
            <div className="flex items-center justify-between pt-2">
              <p className="text-sm text-gray-500">
                Menampilkan {stocks.length} dari {totalCount} saham
                {filter !== 'ALL' && ` (${filter})`}
              </p>
              <div className="flex items-center gap-2">
                <button
                  onClick={() => handlePageChange(page - 1)}
                  disabled={page <= 1}
                  className="p-2 rounded-lg bg-surface-card border border-gray-800 disabled:opacity-30 hover:bg-surface-hover"
                >
                  <ChevronLeft className="w-4 h-4" />
                </button>
                <span className="text-sm text-gray-400 font-mono px-2">
                  {page} / {pages}
                </span>
                <button
                  onClick={() => handlePageChange(page + 1)}
                  disabled={page >= pages}
                  className="p-2 rounded-lg bg-surface-card border border-gray-800 disabled:opacity-30 hover:bg-surface-hover"
                >
                  <ChevronRight className="w-4 h-4" />
                </button>
              </div>
            </div>
          </>
        )}

        {lastUpdated && !scanning && (
          <p className="text-center text-xs text-gray-600">
            Terakhir diperbarui: {lastUpdated.toLocaleString('id-ID')}
          </p>
        )}
      </main>

      <footer className="border-t border-gray-800 mt-8">
        <div className="max-w-7xl mx-auto px-4 py-6 text-center space-y-1">
          <p className="text-sm text-gray-400">
            © {new Date().getFullYear()} DayTrade Pro
          </p>
          <p className="text-xs text-gray-500">
            Created by{' '}
            <span className="text-accent-green font-medium">
              Achmad Maulana Siregar, S.M.
            </span>
          </p>
        </div>
      </footer>
    </div>
  )
}
