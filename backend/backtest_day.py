"""
Backtest rekomendasi day-trade: sinyal dari penutupan Jumat sebelum Senin,
validasi Entry/SL/TP pada hari Senin dan sesi berikutnya.
"""
from __future__ import annotations

import json
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path

import httpx

from indicators import compute_all
from idx_stocks import normalize_ticker
from trade_plan import calculate_trade_plan
from scoring import avg_daily_turnover, determine_action, MIN_DAILY_TURNOVER_IDR
from analyzer import latest_signals, score_stock

HEADERS = {"User-Agent": "Mozilla/5.0"}
YAHOO_CHART = "https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"

# Senin 15 Jun 2026 — sinyal dari penutupan Jumat 12 Jun 2026
SIGNAL_DATE = "2026-06-12"
TRADE_DATES = ["2026-06-15", "2026-06-16", "2026-06-17"]


def ts_to_date(ts: int) -> str:
    return datetime.fromtimestamp(ts, tz=timezone.utc).strftime("%Y-%m-%d")


def fetch_bars(symbol: str, period1: int, period2: int) -> list[dict]:
    url = YAHOO_CHART.format(symbol=symbol)
    params = {"period1": period1, "period2": period2, "interval": "1d"}
    with httpx.Client(timeout=20.0, headers=HEADERS) as client:
        resp = client.get(url, params=params)
        resp.raise_for_status()
        data = resp.json()
    result = data["chart"]["result"][0]
    timestamps = result["timestamp"]
    quote = result["indicators"]["quote"][0]
    bars = []
    for i, ts in enumerate(timestamps):
        close = quote["close"][i]
        if close is None:
            continue
        bars.append({
            "timestamp": ts,
            "date": ts_to_date(ts),
            "open": quote["open"][i],
            "high": quote["high"][i],
            "low": quote["low"][i],
            "close": close,
            "volume": quote["volume"][i] or 0,
        })
    return bars


def analyze_at_index(enriched: list[dict], idx: int) -> dict | None:
    if idx < 29 or idx >= len(enriched):
        return None
    row = enriched[idx]
    prev = enriched[idx - 1]
    signals = latest_signals(row, prev)
    score, reasons, _, _ = score_stock(signals, row, prev)
    avg_turn = avg_daily_turnover(enriched[: idx + 1])
    liquidity_ok = avg_turn >= MIN_DAILY_TURNOVER_IDR
    action, note = determine_action(score, signals, liquidity_ok)
    if note:
        reasons.append(f"○ {note}")
    change_pct = ((row["close"] - prev["close"]) / prev["close"]) * 100 if prev["close"] else 0
    plan = calculate_trade_plan(action, row, enriched[: idx + 1])
    if action == "BUY" and plan.get("risk_reward") is not None:
        from trading_params import DEFAULT_PARAMS
        if plan["risk_reward"] < DEFAULT_PARAMS.min_risk_reward:
            action = "HOLD"
            reasons.append(f"○ R:R {plan['risk_reward']} < {DEFAULT_PARAMS.min_risk_reward}")
            plan = calculate_trade_plan(action, row, enriched[: idx + 1])
    return {
        "score": score,
        "action": action,
        "price": round(row["close"], 2),
        "change_pct": round(change_pct, 2),
        "rsi": round(row["rsi"], 1) if row.get("rsi") is not None else None,
        "liquidity_ok": liquidity_ok,
        "avg_turnover": round(avg_turn, 0),
        "signals": [s["name"] for s in signals if s["type"] == "bullish"],
        "trade_plan": plan,
        "reasons": reasons,
    }


def evaluate_long(entry: float, sl: float, tp1: float, bars: list[dict]) -> dict:
    """Simulasi limit buy long; evaluasi hingga 3 hari trading."""
    filled = False
    fill_price = None
    fill_day = None

    for bar in bars:
        if not filled:
            if bar["low"] <= entry:
                filled = True
                fill_price = entry
                fill_day = bar["date"]
            else:
                continue

        sl_hit = bar["low"] <= sl
        tp_hit = bar["high"] >= tp1

        if sl_hit and tp_hit:
            dist_sl = abs(bar["open"] - sl)
            dist_tp = abs(bar["open"] - tp1)
            outcome = "SL" if dist_sl <= dist_tp else "TP1"
            return {
                "filled": True,
                "fill_price": fill_price,
                "fill_day": fill_day,
                "outcome": outcome,
                "outcome_day": bar["date"],
                "exit_note": f"SL & TP1 keduanya tersentuh; estimasi {'SL' if outcome == 'SL' else 'TP1'} lebih dulu (heuristik open)",
            }
        if sl_hit:
            return {
                "filled": True,
                "fill_price": fill_price,
                "fill_day": fill_day,
                "outcome": "SL",
                "outcome_day": bar["date"],
                "exit_note": "Stop loss tersentuh",
            }
        if tp_hit:
            return {
                "filled": True,
                "fill_price": fill_price,
                "fill_day": fill_day,
                "outcome": "TP1",
                "outcome_day": bar["date"],
                "exit_note": "Take profit 1 tercapai",
            }

    if filled:
        last = bars[-1]
        pnl_pct = round((last["close"] - fill_price) / fill_price * 100, 2)
        return {
            "filled": True,
            "fill_price": fill_price,
            "fill_day": fill_day,
            "outcome": "OPEN",
            "outcome_day": last["date"],
            "exit_note": f"Belum SL/TP; close akhir {last['close']} ({pnl_pct:+.2f}%)",
        }
    return {
        "filled": False,
        "fill_price": None,
        "fill_day": None,
        "outcome": "NO_ENTRY",
        "outcome_day": None,
        "exit_note": "Entry tidak tersentuh (harga tidak turun ke level entry)",
    }


def backtest_ticker(ticker: str, period1: int, period2: int) -> dict | None:
    try:
        ticker = normalize_ticker(ticker)
        bars = fetch_bars(ticker, period1, period2)
        if len(bars) < 35:
            return None

        dates = [b["date"] for b in bars]
        if SIGNAL_DATE not in dates:
            return None

        signal_idx = dates.index(SIGNAL_DATE)
        enriched = compute_all(bars)
        analysis = analyze_at_index(enriched, signal_idx)
        if not analysis or analysis["action"] != "BUY":
            return None

        trade_bars = [b for b in bars if b["date"] in TRADE_DATES]
        if not trade_bars:
            return None

        plan = analysis["trade_plan"]
        eval_result = evaluate_long(plan["entry"], plan["sl"], plan["tp1"], trade_bars)

        mon = next((b for b in trade_bars if b["date"] == TRADE_DATES[0]), None)
        actual = {}
        if mon:
            actual = {
                "open": mon["open"],
                "high": mon["high"],
                "low": mon["low"],
                "close": mon["close"],
                "change_pct": round((mon["close"] - mon["open"]) / mon["open"] * 100, 2),
            }

        code = ticker.replace(".JK", "")
        return {
            "code": code,
            "ticker": ticker,
            "signal_date": SIGNAL_DATE,
            "signal_close": analysis["price"],
            "score": analysis["score"],
            "rsi": analysis["rsi"],
            "signals": analysis["signals"],
            "entry": plan["entry"],
            "sl": plan["sl"],
            "tp1": plan["tp1"],
            "tp2": plan["tp2"],
            "rr": plan["risk_reward"],
            "monday_actual": actual,
            **eval_result,
        }
    except Exception:
        return None


def main():
    period1 = int(datetime(2026, 1, 1, tzinfo=timezone.utc).timestamp())
    period2 = int(datetime(2026, 6, 18, tzinfo=timezone.utc).timestamp())

    stocks_path = Path(__file__).parent / "data" / "ihsg_tickers.json"
    with open(stocks_path) as f:
        tickers = [s["ticker"] for s in json.load(f)["stocks"]]

    print(f"Backtest: sinyal {SIGNAL_DATE} (Jumat) -> trade {', '.join(TRADE_DATES)}")
    print(f"Scanning {len(tickers)} saham...\n")

    results = []
    workers = 12
    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = {pool.submit(backtest_ticker, t, period1, period2): t for t in tickers}
        done = 0
        for fut in as_completed(futures):
            done += 1
            if done % 100 == 0:
                print(f"  ...{done}/{len(tickers)}", flush=True)
            r = fut.result()
            if r:
                results.append(r)

    results.sort(key=lambda x: -x["score"])

    if not results:
        print("Tidak ada sinyal BUY pada tanggal sinyal.")
        return

    outcomes = {"TP1": 0, "SL": 0, "OPEN": 0, "NO_ENTRY": 0}
    for r in results:
        outcomes[r["outcome"]] = outcomes.get(r["outcome"], 0) + 1

    filled = [r for r in results if r["filled"]]
    wins = [r for r in results if r["outcome"] == "TP1"]
    losses = [r for r in results if r["outcome"] == "SL"]

    print("=" * 72)
    print(f"REKOMENDASI BUY - Senin 15 Juni 2026 (sinyal: penutupan {SIGNAL_DATE})")
    print("=" * 72)
    print(f"Total sinyal BUY : {len(results)}")
    print(f"Entry terisi     : {len(filled)}")
    print(f"TP1 tercapai     : {outcomes['TP1']}")
    print(f"Stop loss hit    : {outcomes['SL']}")
    print(f"Masih open       : {outcomes['OPEN']}")
    print(f"Tidak entry      : {outcomes['NO_ENTRY']}")
    if filled:
        win_rate = len(wins) / len(filled) * 100
        print(f"Win rate (filled): {win_rate:.1f}%")
    print()

    hdr = f"{'Kode':<6} {'Skor':>4} {'Entry':>8} {'SL':>8} {'TP1':>8} {'Sen O':>8} {'Sen H':>8} {'Sen L':>8} {'Sen C':>8} {'Hasil':<8} {'Catatan'}"
    print(hdr)
    print("-" * len(hdr))

    for r in results:
        a = r.get("monday_actual") or {}
        print(
            f"{r['code']:<6} {r['score']:>4} {r['entry']:>8.0f} {r['sl']:>8.0f} {r['tp1']:>8.0f} "
            f"{a.get('open', 0):>8.0f} {a.get('high', 0):>8.0f} {a.get('low', 0):>8.0f} {a.get('close', 0):>8.0f} "
            f"{r['outcome']:<8} {r['exit_note'][:40]}"
        )

    print("\n--- Detail per saham ---")
    for r in results:
        a = r.get("monday_actual") or {}
        print(f"\n{r['code']} | Skor {r['score']} | RSI {r['rsi']} | Sinyal: {', '.join(r['signals'])}")
        print(f"  Rekomendasi (Jumat {SIGNAL_DATE} close {r['signal_close']:.0f}):")
        print(f"    Entry {r['entry']:.0f} | SL {r['sl']:.0f} | TP1 {r['tp1']:.0f} | TP2 {r['tp2']:.0f} | R:R {r['rr']}")
        if a:
            print(f"  Aktual Senin 15/06: O={a['open']:.0f} H={a['high']:.0f} L={a['low']:.0f} C={a['close']:.0f} ({a['change_pct']:+.2f}%)")
        print(f"  Simulasi: {r['outcome']} - {r['exit_note']}")
        if r.get("outcome_day"):
            print(f"  Hari keputusan: {r['outcome_day']}")


if __name__ == "__main__":
    main()
