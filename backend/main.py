from pathlib import Path

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

from analyzer import analyze_ticker, get_score_methodology
from idx_stocks import get_all_stocks, get_all_tickers, normalize_ticker, refresh_from_remote
from scan_cache import scan_cache

STATIC_DIR = Path(__file__).parent / "static"

app = FastAPI(
    title="IHSG Day Trading Recommender",
    version="2.0.0",
    description="DayTrade Pro — Created by Achmad Maulana Siregar, S.M.",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.get("/api/stocks")
def list_stocks():
    """Daftar seluruh saham terdaftar IHSG."""
    stocks = get_all_stocks()
    return {
        "market": "IHSG",
        "count": len(stocks),
        "stocks": stocks,
    }


@app.get("/api/analyze/{ticker}")
def analyze(ticker: str):
    result = analyze_ticker(ticker)
    if not result:
        raise HTTPException(status_code=404, detail=f"Data tidak ditemukan untuk {ticker}")
    return result


@app.get("/api/scan/status")
def scan_status():
    return scan_cache.status()


@app.post("/api/scan/refresh")
def scan_refresh():
    started = scan_cache.start_scan(force=True)
    return {"started": started, **scan_cache.status()}


@app.get("/api/score-info")
def score_info():
    return get_score_methodology()


@app.get("/api/scan")
def scan(
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=200),
    action: str | None = Query(None, description="BUY, SELL, atau HOLD"),
    q: str | None = Query(None, description="Cari kode/nama saham"),
    sort: str = Query("score", description="score, change_pct, volume, turnover, code, price, rsi"),
    order: str = Query("desc", description="asc atau desc"),
    refresh: bool = Query(False),
    liquid_only: bool = Query(False, description="Hanya saham likuid (≥ Rp 5M/hari)"),
):
    if refresh or scan_cache.is_stale():
        scan_cache.start_scan(force=refresh)

    status = scan_cache.status()
    results = scan_cache.get_results()

    if status["status"] == "scanning" and not results:
        return {
            "market": "IHSG",
            "total_listed": len(get_all_tickers()),
            "scan": status,
            "count": 0,
            "page": page,
            "pages": 0,
            "recommendations": [],
        }

    filtered = results
    if liquid_only:
        filtered = [r for r in filtered if r.get("liquidity_ok", False)]

    if action and action.upper() in ("BUY", "SELL", "HOLD"):
        filtered = [r for r in filtered if r["action"] == action.upper()]

    if q:
        q_lower = q.lower()
        filtered = [
            r for r in filtered
            if q_lower in r["code"].lower() or q_lower in r["name"].lower()
        ]

    reverse = order.lower() == "desc"

    sort_key = {
        "score": lambda x: x["score"],
        "change_pct": lambda x: x["change_pct"],
        "volume": lambda x: x["volume"],
        "turnover": lambda x: x.get("avg_turnover", 0),
        "code": lambda x: x["code"],
        "price": lambda x: x["price"],
        "rsi": lambda x: x["rsi"] if x["rsi"] is not None else -1,
        "news_sentiment": lambda x: x.get("news_sentiment", 0),
        "name": lambda x: x["name"].lower(),
        "action": lambda x: {"BUY": 3, "HOLD": 2, "SELL": 1}.get(x["action"], 0),
    }.get(sort, lambda x: x["score"])

    filtered = sorted(filtered, key=sort_key, reverse=reverse)

    total = len(filtered)
    pages = max(1, (total + limit - 1) // limit) if total else 0
    start = (page - 1) * limit
    page_items = filtered[start : start + limit]

    buy = sum(1 for r in results if r["action"] == "BUY")
    sell = sum(1 for r in results if r["action"] == "SELL")
    hold = sum(1 for r in results if r["action"] == "HOLD")

    return {
        "market": "IHSG",
        "total_listed": len(get_all_tickers()),
        "scan": status,
        "summary": {"buy": buy, "sell": sell, "hold": hold, "analyzed": len(results)},
        "count": total,
        "page": page,
        "pages": pages,
        "limit": limit,
        "recommendations": page_items,
    }


@app.post("/api/stocks/refresh-list")
def refresh_stock_list():
    count = refresh_from_remote()
    return {"count": count, "message": f"Daftar IHSG diperbarui: {count} saham"}


def _serve_static(path: str):
    if not STATIC_DIR.exists():
        raise HTTPException(status_code=404, detail="Frontend belum di-build")
    target = (STATIC_DIR / path).resolve()
    if not str(target).startswith(str(STATIC_DIR.resolve())):
        raise HTTPException(status_code=404)
    if target.is_file():
        return FileResponse(target)
    index = STATIC_DIR / "index.html"
    if index.exists():
        return FileResponse(index)
    raise HTTPException(status_code=404)


@app.get("/")
def serve_root():
    return _serve_static("index.html")


@app.get("/{full_path:path}")
def serve_spa(full_path: str):
    if full_path.startswith("api") or full_path.startswith("docs") or full_path.startswith("openapi"):
        raise HTTPException(status_code=404)
    return _serve_static(full_path)