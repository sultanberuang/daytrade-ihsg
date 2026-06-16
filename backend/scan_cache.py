import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone

from analyzer import analyze_ticker
from idx_stocks import get_all_tickers

CACHE_TTL_SECONDS = 900  # 15 menit


class ScanCache:
    def __init__(self):
        self._lock = threading.Lock()
        self._status = "idle"
        self._progress = 0
        self._total = 0
        self._results: list[dict] = []
        self._failed: list[str] = []
        self._updated_at: datetime | None = None
        self._error: str | None = None

    def status(self) -> dict:
        with self._lock:
            return {
                "status": self._status,
                "progress": self._progress,
                "total": self._total,
                "count": len(self._results),
                "failed": len(self._failed),
                "updated_at": self._updated_at.isoformat() if self._updated_at else None,
                "error": self._error,
            }

    def get_results(self) -> list[dict]:
        with self._lock:
            return list(self._results)

    def _is_stale_unlocked(self) -> bool:
        if not self._updated_at or self._status != "ready":
            return True
        if self._results and "turnover" not in self._results[0]:
            return True
        age = (datetime.now(timezone.utc) - self._updated_at).total_seconds()
        return age > CACHE_TTL_SECONDS

    def is_stale(self) -> bool:
        with self._lock:
            return self._is_stale_unlocked()

    def start_scan(self, force: bool = False) -> bool:
        with self._lock:
            if self._status == "scanning":
                return False
            if not force and not self._is_stale_unlocked():
                return False
            self._status = "scanning"
            self._progress = 0
            self._total = len(get_all_tickers())
            self._results = []
            self._failed = []
            self._error = None

        thread = threading.Thread(target=self._run_scan, daemon=True)
        thread.start()
        return True

    def _run_scan(self):
        tickers = get_all_tickers()
        total = len(tickers)

        with self._lock:
            self._total = total

        results = []
        failed = []
        done = 0

        with ThreadPoolExecutor(max_workers=12) as pool:
            futures = {pool.submit(analyze_ticker, t): t for t in tickers}
            for future in as_completed(futures):
                ticker = futures[future]
                done += 1
                try:
                    result = future.result()
                    if result:
                        results.append(result)
                    else:
                        failed.append(ticker)
                except Exception:
                    failed.append(ticker)

                with self._lock:
                    self._progress = done
                    if done % 20 == 0:
                        self._results = sorted(results, key=lambda x: x["score"], reverse=True)

        results.sort(key=lambda x: x["score"], reverse=True)

        with self._lock:
            self._results = results
            self._failed = failed
            self._status = "ready"
            self._progress = total
            self._updated_at = datetime.now(timezone.utc)


scan_cache = ScanCache()
