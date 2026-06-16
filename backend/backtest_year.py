"""
Backtest tahunan / YTD: sinyal penutupan H-1, validasi Entry/SL/TP hari trade.
Usage: python backtest_year.py [YYYY]   (default: 2026)
"""
from __future__ import annotations

import json
import sys
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path

from backtest_day import analyze_at_index, evaluate_long, fetch_bars
from backtest_month import process_ticker, summarize

MONTH_NAMES = [
    "", "Jan", "Feb", "Mar", "Apr", "Mei", "Jun",
    "Jul", "Agu", "Sep", "Okt", "Nov", "Des",
]


def build_trading_pairs_year(year: int) -> list[tuple[str, str]]:
    period1 = int(datetime(year - 1, 11, 1, tzinfo=timezone.utc).timestamp())
    period2 = int(datetime(year + 1, 1, 1, tzinfo=timezone.utc).timestamp())
    bars = fetch_bars("BBRI.JK", period1, period2)
    all_dates = [b["date"] for b in bars]
    prefix = f"{year}-"

    pairs = []
    for i, d in enumerate(all_dates):
        if not d.startswith(prefix) or i == 0:
            continue
        pairs.append((all_dates[i - 1], d))
    return pairs


def print_yearly_report(
    all_results: list[dict],
    trading_days: list[tuple[str, str]],
    title: str,
    tier_filter: str | None,
):
    if tier_filter == "BUY":
        filtered = [r for r in all_results if r["tier"] == "BUY"]
    elif tier_filter == "NEAR":
        filtered = [r for r in all_results if r["tier"] == "NEAR"]
    else:
        filtered = all_results

    print("\n" + "#" * 90)
    print(f"# {title}")
    print("#" * 90)

    n_days = len(trading_days)
    total = summarize(filtered)
    date_from = trading_days[0][1]
    date_to = trading_days[-1][1]

    print(f"\nPeriode trade          : {date_from} s/d {date_to}")
    print(f"Hari trading           : {n_days}")
    print(f"Total rekomendasi      : {total['total']}")
    print(f"Rata-rata per hari     : {total['total'] / n_days:.1f}")
    if total["total"]:
        print(f"Entry terisi           : {total['filled']} ({total['filled'] / total['total'] * 100:.0f}%)")
    print(f"TP1 tercapai           : {total['tp1']}")
    print(f"Stop loss              : {total['sl']}")
    print(f"Open (close hari)      : {total['open']}")
    print(f"Tidak entry            : {total['no_entry']}")
    if total["filled"]:
        print(f"Win rate (filled)      : {total['win_rate']}%")
        loss_rate = round(total["sl"] / total["filled"] * 100, 1)
        print(f"Loss rate (filled)     : {loss_rate}%")
    if total["open"]:
        print(f"Rata-rata PnL OPEN     : {total['avg_open_pnl']:+.2f}%")

    # Monthly breakdown
    by_month: dict[str, list[dict]] = defaultdict(list)
    for r in filtered:
        by_month[r["trade_date"][:7]].append(r)

    print(f"\n{'Bulan':<8} {'Hari':>5} {'Rec':>5} {'Fill':>5} {'TP1':>4} {'SL':>4} {'Open':>5} {'NoEnt':>5} {'WR%':>5} {'PnL O':>7}")
    print("-" * 68)
    months_in_data = sorted({td[:7] for _, td in trading_days})
    for ym in months_in_data:
        month_results = by_month.get(ym, [])
        days_in_month = sum(1 for _, td in trading_days if td.startswith(ym))
        s = summarize(month_results)
        wr = f"{s['win_rate']:.0f}" if s["filled"] else "-"
        pnl = f"{s['avg_open_pnl']:+.1f}" if s["open"] else "-"
        y, m = map(int, ym.split("-"))
        print(
            f"{MONTH_NAMES[m]:<8} {days_in_month:>5} {s['total']:>5} {s['filled']:>5} {s['tp1']:>4} {s['sl']:>4} "
            f"{s['open']:>5} {s['no_entry']:>5} {wr:>5} {pnl:>7}"
        )

    # Top / bottom days by win rate (min 3 rec)
    by_day: dict[str, list[dict]] = defaultdict(list)
    for r in filtered:
        by_day[r["trade_date"]].append(r)

    day_stats = []
    for td, recs in by_day.items():
        if len(recs) < 3:
            continue
        s = summarize(recs)
        if s["filled"]:
            day_stats.append((td, s))

    if day_stats:
        best = sorted(day_stats, key=lambda x: (-x[1]["win_rate"], -x[1]["tp1"]))[:5]
        worst = sorted(day_stats, key=lambda x: (x[1]["win_rate"], -x[1]["sl"]))[:5]

        print("\nHari terbaik (min 3 rekom, by win rate):")
        for td, s in best:
            print(f"  {td}  rec={s['total']} TP1={s['tp1']} SL={s['sl']} WR={s['win_rate']}%")

        print("\nHari terburuk (min 3 rekom, by win rate):")
        for td, s in worst:
            print(f"  {td}  rec={s['total']} TP1={s['tp1']} SL={s['sl']} WR={s['win_rate']}%")

    tp1s = [r for r in filtered if r["outcome"] == "TP1"]
    sls = [r for r in filtered if r["outcome"] == "SL"]
    if tp1s:
        print(f"\nTP1 tercapai ({len(tp1s)} total, top 20):")
        for r in sorted(tp1s, key=lambda x: -x["score"])[:20]:
            a = r["actual"]
            print(f"  {r['trade_date']} {r['code']:<6} {r['tier']:<5} skor={r['score']} entry={r['entry']:.0f} TP1={r['tp1']:.0f} H={a['high']:.0f}")
        if len(tp1s) > 20:
            print(f"  ... +{len(tp1s) - 20} lainnya")

    if sls:
        print(f"\nStop loss ({len(sls)} total, top 20 by score):")
        for r in sorted(sls, key=lambda x: -x["score"])[:20]:
            a = r["actual"]
            print(f"  {r['trade_date']} {r['code']:<6} {r['tier']:<5} skor={r['score']} entry={r['entry']:.0f} SL={r['sl']:.0f} L={a['low']:.0f}")
        if len(sls) > 20:
            print(f"  ... +{len(sls) - 20} lainnya")


def main():
    year = int(sys.argv[1]) if len(sys.argv) > 1 else 2026

    trading_days = build_trading_pairs_year(year)
    if not trading_days:
        print(f"Tidak ada hari trading untuk {year}")
        return

    period1 = int(datetime(year - 1, 11, 1, tzinfo=timezone.utc).timestamp())
    period2 = int(datetime(year + 1, 1, 1, tzinfo=timezone.utc).timestamp())

    stocks_path = Path(__file__).parent / "data" / "ihsg_tickers.json"
    with open(stocks_path) as f:
        tickers = [s["ticker"] for s in json.load(f)["stocks"]]

    print(f"Backtest tahun {year} (YTD) | {len(trading_days)} hari trading | {len(tickers)} saham")
    print(f"Trade: {trading_days[0][1]} .. {trading_days[-1][1]}")

    all_results: list[dict] = []
    with ThreadPoolExecutor(max_workers=12) as pool:
        futures = [pool.submit(process_ticker, t, period1, period2, trading_days) for t in tickers]
        done = 0
        for fut in as_completed(futures):
            done += 1
            if done % 200 == 0:
                print(f"  ...{done}/{len(tickers)}", flush=True)
            all_results.extend(fut.result())

    print_yearly_report(all_results, trading_days, f"BUY RESMI (skor >= 75) - {year}", "BUY")
    print_yearly_report(all_results, trading_days, f"SEMUA NEAR-BUY+ (skor >= 72) - {year}", None)
    print_yearly_report(all_results, trading_days, f"Hanya NEAR tier - {year}", "NEAR")


if __name__ == "__main__":
    main()
