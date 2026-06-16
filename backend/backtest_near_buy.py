"""Backtest kandidat near-BUY (skor 72, syarat lain terpenuhi) untuk Senin 15 Jun 2026."""
import json
from datetime import datetime, timezone

from backtest_day import (
    SIGNAL_DATE, TRADE_DATES, fetch_bars, analyze_at_index, evaluate_long,
)
from indicators import compute_all
from idx_stocks import normalize_ticker

period1 = int(datetime(2026, 1, 1, tzinfo=timezone.utc).timestamp())
period2 = int(datetime(2026, 6, 18, tzinfo=timezone.utc).timestamp())

NEAR_BUY_CODES = ["BAIK", "BNBR", "BULL", "CYBR", "IATA", "KLBF", "MARK", "MBSS"]


def qualifies_near_buy(analysis: dict) -> bool:
    if analysis["score"] < 72:
        return False
    if not analysis["liquidity_ok"]:
        return False
    if len(analysis["signals"]) < 2:
        return False
    return analysis["action"] == "HOLD"  # would be BUY if score >= 75


def run():
    print(f"Kandidat near-BUY (skor 72, likuid, 2+ sinyal bullish, konfirmasi tren)")
    print(f"Sinyal: penutupan {SIGNAL_DATE} | Validasi: {TRADE_DATES[0]} (data Yahoo terbaru)\n")

    results = []
    for code in NEAR_BUY_CODES:
        ticker = normalize_ticker(code)
        bars = fetch_bars(ticker, period1, period2)
        dates = [b["date"] for b in bars]
        idx = dates.index(SIGNAL_DATE)
        enriched = compute_all(bars)
        analysis = analyze_at_index(enriched, idx)
        if not analysis or not qualifies_near_buy(analysis):
            print(f"{code}: skip (tidak memenuhi kriteria)")
            continue

        plan = analysis["trade_plan"]
        trade_bars = [b for b in bars if b["date"] in TRADE_DATES]
        ev = evaluate_long(plan["entry"], plan["sl"], plan["tp1"], trade_bars)
        mon = next(b for b in trade_bars if b["date"] == TRADE_DATES[0])

        results.append({
            "code": code,
            "score": analysis["score"],
            "signals": analysis["signals"],
            "signal_close": analysis["price"],
            "entry": plan["entry"],
            "sl": plan["sl"],
            "tp1": plan["tp1"],
            "tp2": plan["tp2"],
            "rr": plan["risk_reward"],
            "mon": mon,
            **ev,
        })

    print("=" * 80)
    print(f"{'Kode':<6} {'Skor':>4} {'Entry':>7} {'SL':>7} {'TP1':>7} | {'Sen O':>7} {'H':>7} {'L':>7} {'C':>7} | {'Hasil':<8}")
    print("-" * 80)
    for r in results:
        m = r["mon"]
        print(
            f"{r['code']:<6} {r['score']:>4} {r['entry']:>7.0f} {r['sl']:>7.0f} {r['tp1']:>7.0f} | "
            f"{m['open']:>7.0f} {m['high']:>7.0f} {m['low']:>7.0f} {m['close']:>7.0f} | {r['outcome']:<8}"
        )

    tp = sum(1 for r in results if r["outcome"] == "TP1")
    sl = sum(1 for r in results if r["outcome"] == "SL")
    filled = sum(1 for r in results if r["filled"])
    print(f"\nRingkasan: {len(results)} kandidat | Entry terisi {filled} | TP1={tp} SL={sl}")

    print("\n--- Analisis akurasi ---")
    for r in results:
        m = r["mon"]
        entry_ok = m["low"] <= r["entry"]
        sl_touch = m["low"] <= r["sl"]
        tp_touch = m["high"] >= r["tp1"]
        print(f"\n{r['code']} (skor {r['score']}, sinyal: {', '.join(r['signals'])})")
        print(f"  Jumat close: {r['signal_close']:.0f}")
        print(f"  Plan: Entry {r['entry']:.0f} | SL {r['sl']:.0f} | TP1 {r['tp1']:.0f} | R:R {r['rr']}")
        print(f"  Senin aktual: O={m['open']:.0f} H={m['high']:.0f} L={m['low']:.0f} C={m['close']:.0f}")
        print(f"  Entry reachable: {'Ya' if entry_ok else 'Tidak'} | SL tersentuh: {'Ya' if sl_touch else 'Tidak'} | TP1 tersentuh: {'Ya' if tp_touch else 'Tidak'}")
        print(f"  Hasil simulasi: {r['outcome']} - {r['exit_note']}")

        # Entry accuracy
        if entry_ok:
            slip = (m["open"] - r["entry"]) / r["entry"] * 100 if m["open"] > r["entry"] else 0
            print(f"  Entry accuracy: limit {r['entry']:.0f} terisi (open {m['open']:.0f}, gap {slip:+.2f}%)")
        else:
            gap = (m["low"] - r["entry"]) / r["entry"] * 100
            print(f"  Entry accuracy: TIDAK terisi - low {m['low']:.0f} masih {gap:+.2f}% di atas entry")


if __name__ == "__main__":
    run()
