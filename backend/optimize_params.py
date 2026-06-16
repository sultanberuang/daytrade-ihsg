"""
Grid search parameter trading vs backtest YTD 2026.
Usage: python optimize_params.py
"""
from __future__ import annotations

import itertools
import json
import time
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import replace
from datetime import datetime, timezone
from pathlib import Path

from analyzer import latest_signals, score_stock
from backtest_day import evaluate_long, fetch_bars
from backtest_year import build_trading_pairs_year
from indicators import compute_all
from idx_stocks import normalize_ticker
from scoring import avg_daily_turnover, determine_action
from trade_plan import calculate_trade_plan
from trading_params import TradingParams, DEFAULT_PARAMS


def preload_ticker(ticker: str, period1: int, period2: int, trading_days: list[tuple[str, str]]):
    """Muat data & precompute skor/sinyal per pasangan (signal, trade)."""
    out = []
    try:
        ticker = normalize_ticker(ticker)
        bars = fetch_bars(ticker, period1, period2)
        if len(bars) < 35:
            return out

        dates = [b["date"] for b in bars]
        date_index = {d: i for i, d in enumerate(dates)}
        bar_by_date = {b["date"]: b for b in bars}
        enriched = compute_all(bars)
        code = ticker.replace(".JK", "")

        by_signal: dict[str, list[str]] = defaultdict(list)
        for sig, td in trading_days:
            by_signal[sig].append(td)

        for sig_date, trade_dates in by_signal.items():
            if sig_date not in date_index:
                continue
            idx = date_index[sig_date]
            if idx < 29:
                continue
            row = enriched[idx]
            prev = enriched[idx - 1]
            signals = latest_signals(row, prev)
            score, _, _, _ = score_stock(signals, row, prev)
            avg_turn = avg_daily_turnover(enriched[: idx + 1])
            base = {
                "code": code,
                "signal_date": sig_date,
                "score": score,
                "signals": signals,
                "liquidity_ok": avg_turn >= DEFAULT_PARAMS.min_daily_turnover,
                "row": row,
                "enriched": enriched[: idx + 1],
            }
            for td in trade_dates:
                if td in bar_by_date:
                    out.append({**base, "trade_date": td, "trade_bar": bar_by_date[td]})
    except Exception:
        pass
    return out


def preload_all(tickers: list[str], period1: int, period2: int, trading_days: list[tuple[str, str]]):
    rows = []
    with ThreadPoolExecutor(max_workers=12) as pool:
        futs = [pool.submit(preload_ticker, t, period1, period2, trading_days) for t in tickers]
        done = 0
        for fut in as_completed(futs):
            done += 1
            if done % 200 == 0:
                print(f"  preload {done}/{len(tickers)}", flush=True)
            rows.extend(fut.result())
    return rows


def evaluate_entry(entry: float, trade_bar: dict, max_gap_pct: float) -> tuple[bool, float]:
    """Limit buy + fallback market di open jika gap kecil."""
    if trade_bar["low"] <= entry:
        return True, entry
    if entry <= 0:
        return False, entry
    gap_pct = (trade_bar["open"] - entry) / entry * 100
    if 0 < gap_pct <= max_gap_pct:
        return True, trade_bar["open"]
    return False, entry


def simulate(snapshots: list[dict], params: TradingParams) -> dict:
    tp1 = sl = open_ = no_entry = filled = total = 0
    open_pnls = []

    for snap in snapshots:
        action, _ = determine_action(
            snap["score"], snap["signals"], snap["liquidity_ok"], params
        )
        if action != "BUY":
            continue

        plan = calculate_trade_plan(action, snap["row"], snap["enriched"], params)
        if plan["risk_reward"] is not None and plan["risk_reward"] < params.min_risk_reward:
            continue
        if plan["sl"] >= plan["entry"]:
            continue

        total += 1
        bar = snap["trade_bar"]
        is_filled, fill_price = evaluate_entry(plan["entry"], bar, params.max_gap_entry_pct)

        if not is_filled:
            no_entry += 1
            continue

        filled += 1
        sl_hit = bar["low"] <= plan["sl"]
        tp_hit = bar["high"] >= plan["tp1"]

        if sl_hit and tp_hit:
            dist_sl = abs(bar["open"] - plan["sl"])
            dist_tp = abs(bar["open"] - plan["tp1"])
            if dist_sl <= dist_tp:
                sl += 1
            else:
                tp1 += 1
        elif sl_hit:
            sl += 1
        elif tp_hit:
            tp1 += 1
        else:
            open_ += 1
            open_pnls.append((bar["close"] - fill_price) / fill_price * 100)

    wr = tp1 / filled * 100 if filled else 0
    sl_rate = sl / filled * 100 if filled else 0
    avg_open = sum(open_pnls) / len(open_pnls) if open_pnls else 0
    return {
        "total": total,
        "filled": filled,
        "tp1": tp1,
        "sl": sl,
        "open": open_,
        "no_entry": no_entry,
        "win_rate": round(wr, 1),
        "sl_rate": round(sl_rate, 1),
        "avg_open_pnl": round(avg_open, 2),
    }


def fitness(stats: dict, n_days: int) -> float:
    if stats["filled"] < 40:
        return -999.0
    per_day = stats["total"] / n_days
    if per_day < 0.3 or per_day > 15:
        return -500.0
    return (
        stats["win_rate"] * 0.40
        + (stats["tp1"] / stats["filled"] * 100) * 0.20
        - stats["sl_rate"] * 0.25
        + stats["avg_open_pnl"] * 3.0
        - abs(per_day - 3.0) * 2.0
    )


def main():
    year = 2026
    trading_days = build_trading_pairs_year(year)
    n_days = len(trading_days)

    period1 = int(datetime(year - 1, 11, 1, tzinfo=timezone.utc).timestamp())
    period2 = int(datetime(year + 1, 1, 1, tzinfo=timezone.utc).timestamp())

    with open(Path(__file__).parent / "data" / "ihsg_tickers.json") as f:
        tickers = [s["ticker"] for s in json.load(f)["stocks"]]

    print(f"Optimasi parameter | {n_days} hari trading | {len(tickers)} saham")
    t0 = time.time()
    snapshots = preload_all(tickers, period1, period2, trading_days)
    print(f"Preload selesai: {len(snapshots)} baris sinyal ({time.time() - t0:.0f}s)\n")

    grid = {
        "min_buy_score": [72, 75, 78],
        "min_bullish_signals": [2, 3],
        "sl_atr_mult": [1.5, 2.0, 2.5],
        "tp1_atr_mult": [0.8, 1.0, 1.2],
        "min_risk_reward": [0.8, 1.0, 1.5],
        "max_gap_entry_pct": [2.0, 3.0],
    }

    keys = list(grid.keys())
    combos = list(itertools.product(*grid.values()))
    print(f"Grid search: {len(combos)} kombinasi...\n")

    baseline = simulate(snapshots, DEFAULT_PARAMS)
    baseline["fitness"] = fitness(baseline, n_days)
    print(f"Baseline: {baseline} fitness={baseline['fitness']:.1f}\n")

    results = []
    for i, vals in enumerate(combos):
        kw = dict(zip(keys, vals))
        p = replace(DEFAULT_PARAMS, **kw)
        stats = simulate(snapshots, p)
        stats["fitness"] = fitness(stats, n_days)
        stats["params"] = kw
        results.append(stats)
        if (i + 1) % 100 == 0:
            print(f"  ...{i + 1}/{len(combos)}", flush=True)

    results.sort(key=lambda x: -x["fitness"])

    print(f"\n{'=' * 100}")
    print("TOP 10 PARAMETER SETS")
    print(f"{'=' * 100}")
    hdr = f"{'#':>3} {'fit':>6} {'WR%':>5} {'SL%':>5} {'Rec':>5} {'Fill':>5} {'TP1':>4} {'SL':>4} {'Open':>5} {'PnL':>6}  Params"
    print(hdr)
    print("-" * len(hdr))
    for i, r in enumerate(results[:10], 1):
        p = r["params"]
        pstr = f"sc={p['min_buy_score']} sig={p['min_bullish_signals']} sl={p['sl_atr_mult']} tp={p['tp1_atr_mult']} rr={p['min_risk_reward']} gap={p['max_gap_entry_pct']}"
        print(
            f"{i:>3} {r['fitness']:>6.1f} {r['win_rate']:>5.1f} {r['sl_rate']:>5.1f} {r['total']:>5} "
            f"{r['filled']:>5} {r['tp1']:>4} {r['sl']:>4} {r['open']:>5} {r['avg_open_pnl']:>+5.2f}%  {pstr}"
        )

    best = results[0]
    print(f"\nBEST PARAMS: {best['params']}")
    print(f"Stats: { {k: best[k] for k in ('total','filled','tp1','sl','open','no_entry','win_rate','sl_rate','avg_open_pnl')} }")

    out_path = Path(__file__).parent / "optimized_params.json"
    with open(out_path, "w") as f:
        json.dump({"baseline": baseline, "best": best}, f, indent=2)
    print(f"\nSaved: {out_path}")


if __name__ == "__main__":
    main()
