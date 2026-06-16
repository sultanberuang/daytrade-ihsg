"""
Backtest bulanan: sinyal penutupan H-1, validasi Entry/SL/TP pada hari trade.
Usage: python backtest_month.py [YYYY-MM]   (default: 2026-05)
"""
from __future__ import annotations

import json
import sys
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path

from backtest_day import analyze_at_index, evaluate_long, fetch_bars
from indicators import compute_all
from idx_stocks import normalize_ticker

MIN_SCORE_NEAR = 72


def has_trend(signals: list[str]) -> bool:
    trend_names = {"MACD Bullish Cross", "Price Above EMA9/21", "Volume Spike"}
    return any(s in trend_names for s in signals)


def qualifies_near_buy(analysis: dict) -> bool:
    if analysis["score"] < MIN_SCORE_NEAR:
        return False
    if not analysis["liquidity_ok"]:
        return False
    if len(analysis["signals"]) < 2:
        return False
    return has_trend(analysis["signals"])


def build_trading_pairs(year: int, month: int) -> list[tuple[str, str]]:
    """Bangun pasangan (signal_date, trade_date) dari kalender Yahoo."""
    period1 = int(datetime(year, month - 1 if month > 1 else year - 1, month - 1 if month > 1 else 12, 1, tzinfo=timezone.utc).timestamp())
    period2 = int(datetime(year, month + 1 if month < 12 else year + 1, 1, tzinfo=timezone.utc).timestamp())
    bars = fetch_bars("BBRI.JK", period1, period2)
    all_dates = [b["date"] for b in bars]
    prefix = f"{year}-{month:02d}"

    pairs = []
    for i, d in enumerate(all_dates):
        if not d.startswith(prefix) or i == 0:
            continue
        pairs.append((all_dates[i - 1], d))
    return pairs


def process_ticker(ticker: str, period1: int, period2: int, trading_days: list[tuple[str, str]]) -> list[dict]:
    results = []
    try:
        ticker = normalize_ticker(ticker)
        bars = fetch_bars(ticker, period1, period2)
        if len(bars) < 35:
            return results

        dates = [b["date"] for b in bars]
        date_index = {d: i for i, d in enumerate(dates)}
        bar_by_date = {b["date"]: b for b in bars}
        enriched = compute_all(bars)
        code = ticker.replace(".JK", "")

        for signal_date, trade_date in trading_days:
            if signal_date not in date_index or trade_date not in date_index:
                continue

            analysis = analyze_at_index(enriched, date_index[signal_date])
            if not analysis:
                continue

            official = analysis["action"] == "BUY"
            near = qualifies_near_buy(analysis) and not official
            if not official and not near:
                continue

            plan = analysis["trade_plan"]
            trade_bar = bar_by_date[trade_date]
            ev = evaluate_long(plan["entry"], plan["sl"], plan["tp1"], [trade_bar])

            pnl_close = None
            if ev["filled"] and ev["outcome"] == "OPEN":
                pnl_close = round((trade_bar["close"] - ev["fill_price"]) / ev["fill_price"] * 100, 2)

            results.append({
                "code": code,
                "trade_date": trade_date,
                "signal_date": signal_date,
                "tier": "BUY" if official else "NEAR",
                "score": analysis["score"],
                "entry": plan["entry"],
                "sl": plan["sl"],
                "tp1": plan["tp1"],
                "actual": trade_bar,
                "pnl_close": pnl_close,
                **ev,
            })
    except Exception:
        pass
    return results


def summarize(results: list[dict]) -> dict:
    filled = [r for r in results if r["filled"]]
    open_pnl = [r["pnl_close"] for r in results if r.get("pnl_close") is not None]
    return {
        "total": len(results),
        "filled": len(filled),
        "tp1": sum(1 for r in results if r["outcome"] == "TP1"),
        "sl": sum(1 for r in results if r["outcome"] == "SL"),
        "open": sum(1 for r in results if r["outcome"] == "OPEN"),
        "no_entry": sum(1 for r in results if r["outcome"] == "NO_ENTRY"),
        "win_rate": round(sum(1 for r in filled if r["outcome"] == "TP1") / len(filled) * 100, 1) if filled else 0,
        "avg_open_pnl": round(sum(open_pnl) / len(open_pnl), 2) if open_pnl else 0,
    }


def print_report(all_results: list[dict], trading_days: list[tuple[str, str]], title: str, tier_filter: str | None):
    if tier_filter == "BUY":
        filtered = [r for r in all_results if r["tier"] == "BUY"]
    elif tier_filter == "NEAR":
        filtered = [r for r in all_results if r["tier"] == "NEAR"]
    else:
        filtered = all_results if tier_filter is None else [r for r in all_results if r["tier"] == tier_filter]

    print("\n" + "#" * 90)
    print(f"# {title}")
    print("#" * 90)

    by_day: dict[str, list[dict]] = defaultdict(list)
    for r in filtered:
        by_day[r["trade_date"]].append(r)

    n_days = len(trading_days)
    total = summarize(filtered)

    print(f"\nTotal rekomendasi ({n_days} hari) : {total['total']}")
    print(f"Rata-rata per hari               : {total['total'] / n_days:.1f}")
    if total["total"]:
        print(f"Entry terisi                     : {total['filled']} ({total['filled'] / total['total'] * 100:.0f}%)")
    print(f"TP1 tercapai                     : {total['tp1']}")
    print(f"Stop loss                        : {total['sl']}")
    print(f"Open (close hari)                : {total['open']}")
    print(f"Tidak entry                      : {total['no_entry']}")
    if total["filled"]:
        print(f"Win rate (filled)                : {total['win_rate']}%")
    if total["open"]:
        print(f"Rata-rata PnL posisi OPEN        : {total['avg_open_pnl']:+.2f}%")

    # Weekly buckets
    by_week: dict[int, list[dict]] = defaultdict(list)
    for r in filtered:
        week = datetime.strptime(r["trade_date"], "%Y-%m-%d").isocalendar()[1]
        by_week[week].append(r)

    print(f"\n{'Minggu':<8} {'Rec':>5} {'Fill':>5} {'TP1':>4} {'SL':>4} {'Open':>5} {'NoEnt':>5} {'WR%':>5}")
    print("-" * 50)
    for week in sorted(by_week):
        s = summarize(by_week[week])
        wr = f"{s['win_rate']:.0f}" if s["filled"] else "-"
        print(f"W{week:<7} {s['total']:>5} {s['filled']:>5} {s['tp1']:>4} {s['sl']:>4} {s['open']:>5} {s['no_entry']:>5} {wr:>5}")

    print(f"\n{'Tanggal':<12} {'Sinyal':<12} {'Rec':>4} {'Fill':>5} {'TP1':>4} {'SL':>4} {'Open':>5} {'NoEnt':>5} {'WR%':>5}")
    print("-" * 65)
    for sig, td in trading_days:
        s = summarize(by_day.get(td, []))
        wr = f"{s['win_rate']:.0f}" if s["filled"] else "-"
        print(
            f"{td:<12} {sig:<12} {s['total']:>4} {s['filled']:>5} {s['tp1']:>4} {s['sl']:>4} "
            f"{s['open']:>5} {s['no_entry']:>5} {wr:>5}"
        )

    # Top wins / losses
    tp1s = [r for r in filtered if r["outcome"] == "TP1"]
    sls = [r for r in filtered if r["outcome"] == "SL"]
    if tp1s:
        print(f"\nTP1 tercapai ({len(tp1s)}):")
        for r in sorted(tp1s, key=lambda x: -x["score"])[:15]:
            a = r["actual"]
            print(f"  {r['trade_date']} {r['code']:<6} {r['tier']:<5} skor={r['score']} entry={r['entry']:.0f} TP1={r['tp1']:.0f} H={a['high']:.0f}")
        if len(tp1s) > 15:
            print(f"  ... +{len(tp1s) - 15} lainnya")
    if sls:
        print(f"\nStop loss ({len(sls)}):")
        for r in sorted(sls, key=lambda x: -x["score"])[:15]:
            a = r["actual"]
            print(f"  {r['trade_date']} {r['code']:<6} {r['tier']:<5} skor={r['score']} entry={r['entry']:.0f} SL={r['sl']:.0f} L={a['low']:.0f}")


def main():
    month_arg = sys.argv[1] if len(sys.argv) > 1 else "2026-05"
    year, month = map(int, month_arg.split("-"))

    trading_days = build_trading_pairs(year, month)
    if not trading_days:
        print(f"Tidak ada hari trading untuk {month_arg}")
        return

    period1 = int(datetime(year, month - 2 if month > 2 else year - 1, month - 2 if month > 2 else 12, 1, tzinfo=timezone.utc).timestamp())
    period2 = int(datetime(year, month + 1 if month < 12 else year + 1, 1, tzinfo=timezone.utc).timestamp())

    stocks_path = Path(__file__).parent / "data" / "ihsg_tickers.json"
    with open(stocks_path) as f:
        tickers = [s["ticker"] for s in json.load(f)["stocks"]]

    print(f"Backtest bulan {month_arg} | {len(trading_days)} hari trading | {len(tickers)} saham")
    print(f"Periode sinyal: {trading_days[0][0]} .. {trading_days[-1][0]}")

    all_results: list[dict] = []
    with ThreadPoolExecutor(max_workers=12) as pool:
        futures = [pool.submit(process_ticker, t, period1, period2, trading_days) for t in tickers]
        done = 0
        for fut in as_completed(futures):
            done += 1
            if done % 200 == 0:
                print(f"  ...{done}/{len(tickers)}", flush=True)
            all_results.extend(fut.result())

    month_name = datetime(year, month, 1).strftime("%B %Y")
    print_report(all_results, trading_days, f"BUY RESMI (skor >= 75) - {month_name}", "BUY")
    print_report(all_results, trading_days, f"NEAR-BUY (skor >= 72) - {month_name}", None)
    print_report(all_results, trading_days, f"Hanya NEAR-BUY tier - {month_name}", "NEAR")


if __name__ == "__main__":
    main()
