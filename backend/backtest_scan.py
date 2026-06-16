"""Quick scan of actions on signal date."""
import json
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone

from backtest_day import fetch_bars, analyze_at_index, SIGNAL_DATE
from indicators import compute_all
from idx_stocks import normalize_ticker

period1 = int(datetime(2026, 1, 1, tzinfo=timezone.utc).timestamp())
period2 = int(datetime(2026, 6, 18, tzinfo=timezone.utc).timestamp())


def check(ticker):
    try:
        ticker = normalize_ticker(ticker)
        bars = fetch_bars(ticker, period1, period2)
        dates = [b["date"] for b in bars]
        if SIGNAL_DATE not in dates:
            return None
        idx = dates.index(SIGNAL_DATE)
        e = compute_all(bars)
        a = analyze_at_index(e, idx)
        if not a:
            return None
        return {
            "code": ticker.replace(".JK", ""),
            "action": a["action"],
            "score": a["score"],
            "signals": a["signals"],
            "liq": a["liquidity_ok"],
            "plan": a["trade_plan"],
        }
    except Exception:
        return None


with open("data/ihsg_tickers.json") as f:
    tickers = [s["ticker"] for s in json.load(f)["stocks"]]

rows = []
with ThreadPoolExecutor(12) as pool:
    for r in pool.map(check, tickers):
        if r:
            rows.append(r)

c = Counter(r["action"] for r in rows)
print("Actions on", SIGNAL_DATE, dict(c))
print("Top 20 by score:")
for r in sorted(rows, key=lambda x: -x["score"])[:20]:
    print(f"  {r['code']:6} {r['action']:4} score={r['score']} liq={r['liq']} sig={r['signals']}")
print("Score>=75:", len([r for r in rows if r["score"] >= 75]))
