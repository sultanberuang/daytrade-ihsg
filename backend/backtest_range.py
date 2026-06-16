"""
Backtest multi-hari: sinyal dari penutupan H-1, validasi Entry/SL/TP pada hari trade.
Periode: 8-12 Juni 2026 (5 sesi trading).
"""
from __future__ import annotations

import json
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path

from backtest_day import (
    analyze_at_index,
    evaluate_long,
    fetch_bars,
)
from indicators import compute_all
from idx_stocks import normalize_ticker

# (signal_date, trade_date)
TRADING_DAYS = [
    ("2026-06-05", "2026-06-08"),  # Senin
    ("2026-06-08", "2026-06-09"),  # Selasa
    ("2026-06-09", "2026-06-10"),  # Rabu
    ("2026-06-10", "2026-06-11"),  # Kamis
    ("2026-06-11", "2026-06-12"),  # Jumat
]

DAY_LABELS = {
    "2026-06-08": "Sen 08/06",
    "2026-06-09": "Sel 09/06",
    "2026-06-10": "Rab 10/06",
    "2026-06-11": "Kam 11/06",
    "2026-06-12": "Jum 12/06",
}

MIN_SCORE_BUY = 75
MIN_SCORE_NEAR = 72


def has_trend(signals: list[str]) -> bool:
    trend_names = {"MACD Bullish Cross", "Price Above EMA9/21", "Volume Spike"}
    return any(s in trend_names for s in signals)


def qualifies_buy(analysis: dict, min_score: int) -> bool:
    if analysis["score"] < min_score:
        return False
    if not analysis["liquidity_ok"]:
        return False
    if len(analysis["signals"]) < 2:
        return False
    if not has_trend(analysis["signals"]):
        return False
    return True


def process_ticker(ticker: str, period1: int, period2: int, min_score: int) -> list[dict]:
    results = []
    try:
        ticker = normalize_ticker(ticker)
        bars = fetch_bars(ticker, period1, period2)
        if len(bars) < 35:
            return results

        dates = [b["date"] for b in bars]
        date_index = {d: i for i, d in enumerate(dates)}
        enriched = compute_all(bars)
        code = ticker.replace(".JK", "")

        for signal_date, trade_date in TRADING_DAYS:
            if signal_date not in date_index or trade_date not in date_index:
                continue

            analysis = analyze_at_index(enriched, date_index[signal_date])
            if not analysis:
                continue

            official = analysis["action"] == "BUY"
            near = qualifies_buy(analysis, MIN_SCORE_NEAR) and not official
            if min_score == MIN_SCORE_BUY and not official:
                continue
            if min_score == MIN_SCORE_NEAR and not (official or near):
                continue

            plan = analysis["trade_plan"]
            trade_bar = next(b for b in bars if b["date"] == trade_date)
            ev = evaluate_long(plan["entry"], plan["sl"], plan["tp1"], [trade_bar])

            results.append({
                "code": code,
                "trade_date": trade_date,
                "signal_date": signal_date,
                "tier": "BUY" if official else "NEAR",
                "score": analysis["score"],
                "rsi": analysis["rsi"],
                "signals": analysis["signals"],
                "signal_close": analysis["price"],
                "entry": plan["entry"],
                "sl": plan["sl"],
                "tp1": plan["tp1"],
                "rr": plan["risk_reward"],
                "actual": {
                    "open": trade_bar["open"],
                    "high": trade_bar["high"],
                    "low": trade_bar["low"],
                    "close": trade_bar["close"],
                },
                **ev,
            })
    except Exception:
        pass
    return results


def summarize(results: list[dict]) -> dict:
    filled = [r for r in results if r["filled"]]
    return {
        "total": len(results),
        "filled": len(filled),
        "tp1": sum(1 for r in results if r["outcome"] == "TP1"),
        "sl": sum(1 for r in results if r["outcome"] == "SL"),
        "open": sum(1 for r in results if r["outcome"] == "OPEN"),
        "no_entry": sum(1 for r in results if r["outcome"] == "NO_ENTRY"),
        "win_rate": round(sum(1 for r in filled if r["outcome"] == "TP1") / len(filled) * 100, 1) if filled else 0,
    }


def print_day_table(trade_date: str, day_results: list[dict]):
    label = DAY_LABELS.get(trade_date, trade_date)
    sig = day_results[0]["signal_date"] if day_results else "?"
    print(f"\n{'=' * 90}")
    print(f"{label} | sinyal penutupan {sig} | {len(day_results)} rekomendasi")
    print(f"{'=' * 90}")
    if not day_results:
        print("  (tidak ada sinyal)")
        return

    hdr = f"{'Kode':<6} {'Tier':<5} {'Skor':>4} {'Entry':>7} {'SL':>7} {'TP1':>7} | {'O':>7} {'H':>7} {'L':>7} {'C':>7} | {'Hasil':<8}"
    print(hdr)
    print("-" * len(hdr))
    for r in sorted(day_results, key=lambda x: (-x["score"], x["code"])):
        a = r["actual"]
        print(
            f"{r['code']:<6} {r['tier']:<5} {r['score']:>4} {r['entry']:>7.0f} {r['sl']:>7.0f} {r['tp1']:>7.0f} | "
            f"{a['open']:>7.0f} {a['high']:>7.0f} {a['low']:>7.0f} {a['close']:>7.0f} | {r['outcome']:<8}"
        )

    s = summarize(day_results)
    print(
        f"  -> Entry terisi {s['filled']}/{s['total']} | TP1={s['tp1']} SL={s['sl']} "
        f"Open={s['open']} NoEntry={s['no_entry']} | Win rate {s['win_rate']}%"
    )


def main():
    period1 = int(datetime(2026, 4, 1, tzinfo=timezone.utc).timestamp())
    period2 = int(datetime(2026, 6, 18, tzinfo=timezone.utc).timestamp())

    stocks_path = Path(__file__).parent / "data" / "ihsg_tickers.json"
    with open(stocks_path) as f:
        tickers = [s["ticker"] for s in json.load(f)["stocks"]]

    for mode, min_score, title in [
        ("official", MIN_SCORE_BUY, "BUY RESMI (skor >= 75)"),
        ("near", MIN_SCORE_NEAR, "NEAR-BUY (skor >= 72, syarat lain terpenuhi)"),
    ]:
        print("\n" + "#" * 90)
        print(f"# BACKTEST 8-12 JUNI 2026 - {title}")
        print("#" * 90)
        print(f"Scanning {len(tickers)} saham...\n")

        all_results: list[dict] = []
        with ThreadPoolExecutor(max_workers=12) as pool:
            futures = [pool.submit(process_ticker, t, period1, period2, min_score) for t in tickers]
            done = 0
            for fut in as_completed(futures):
                done += 1
                if done % 200 == 0:
                    print(f"  ...{done}/{len(tickers)}", flush=True)
                all_results.extend(fut.result())

        by_day: dict[str, list[dict]] = defaultdict(list)
        for r in all_results:
            by_day[r["trade_date"]].append(r)

        trade_dates = [td for _, td in TRADING_DAYS]
        for td in trade_dates:
            print_day_table(td, by_day.get(td, []))

        total = summarize(all_results)
        print(f"\n{'=' * 90}")
        print(f"RINGKASAN MINGGU ({title})")
        print(f"{'=' * 90}")
        print(f"Total rekomendasi (5 hari) : {total['total']}")
        print(f"Rata-rata per hari         : {total['total'] / 5:.1f}")
        print(f"Entry terisi               : {total['filled']} ({total['filled'] / total['total'] * 100:.0f}%)" if total["total"] else "Entry terisi: 0")
        print(f"TP1 tercapai               : {total['tp1']}")
        print(f"Stop loss                  : {total['sl']}")
        print(f"Masih open (close hari)    : {total['open']}")
        print(f"Tidak entry                : {total['no_entry']}")
        if total["filled"]:
            print(f"Win rate (filled)          : {total['win_rate']}%")

        # Per-day summary row
        print(f"\n{'Hari':<12} {'Sinyal':<12} {'Rec':>4} {'Fill':>5} {'TP1':>4} {'SL':>4} {'Open':>5} {'NoEnt':>5} {'WR%':>5}")
        print("-" * 60)
        for sig, td in TRADING_DAYS:
            s = summarize(by_day.get(td, []))
            label = DAY_LABELS.get(td, td)
            wr = f"{s['win_rate']:.0f}" if s["filled"] else "-"
            print(
                f"{label:<12} {sig:<12} {s['total']:>4} {s['filled']:>5} {s['tp1']:>4} {s['sl']:>4} "
                f"{s['open']:>5} {s['no_entry']:>5} {wr:>5}"
            )


if __name__ == "__main__":
    main()
