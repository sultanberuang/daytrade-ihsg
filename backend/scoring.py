"""Parameter trading & scoring — dikalibrasi via backtest YTD 2026."""
from trading_params import DEFAULT_PARAMS, TREND_BULLISH, TREND_BEARISH, TradingParams

MIN_DAILY_TURNOVER_IDR = DEFAULT_PARAMS.min_daily_turnover

SCORE_METHODOLOGY = {
    "base": 50,
    "weights": {
        "bullish_signal": "+6 per sinyal bullish",
        "bearish_signal": "-6 per sinyal bearish",
        "momentum": "+5 jika perubahan > 2%, -5 jika < -2%",
        "volatility": "+5 jika ATR > 3% dari harga",
        "news_bullish": "+5 s/d +10",
        "news_bearish": "-5 s/d -10",
    },
    "buy_requirements": [
        f"Skor ≥ {DEFAULT_PARAMS.min_buy_score}",
        f"Min. {DEFAULT_PARAMS.min_bullish_signals} sinyal bullish",
        "Konfirmasi tren (MACD cross / harga > EMA9/21 / volume spike)",
        f"Nilai transaksi rata-rata ≥ Rp {DEFAULT_PARAMS.min_daily_turnover / 1e9:.0f} M/hari",
        f"Risk:Reward ≥ {DEFAULT_PARAMS.min_risk_reward}",
    ],
    "sell_requirements": [
        f"Skor ≤ {DEFAULT_PARAMS.min_sell_score}",
        f"Min. {DEFAULT_PARAMS.min_bearish_signals} sinyal bearish",
    ],
    "trade_plan": {
        "sl_atr_mult": DEFAULT_PARAMS.sl_atr_mult,
        "tp1_atr_mult": DEFAULT_PARAMS.tp1_atr_mult,
        "max_gap_entry_pct": DEFAULT_PARAMS.max_gap_entry_pct,
    },
}


def avg_daily_turnover(enriched: list[dict], days: int = 5) -> float:
    recent = enriched[-days:]
    if not recent:
        return 0.0
    return sum(b["close"] * b["volume"] for b in recent) / len(recent)


def build_score_breakdown(
    signals: list[dict],
    momentum_delta: int,
    volatility_delta: int,
    news_delta: int,
    final_score: int,
) -> dict:
    items = [{"label": "Basis", "value": 50, "type": "base"}]

    for sig in signals:
        if sig["type"] == "bullish":
            items.append({"label": sig["name"], "value": 6, "type": "bullish"})
        elif sig["type"] == "bearish":
            items.append({"label": sig["name"], "value": -6, "type": "bearish"})

    if momentum_delta:
        items.append({
            "label": "Momentum harga",
            "value": momentum_delta,
            "type": "bullish" if momentum_delta > 0 else "bearish",
        })
    if volatility_delta:
        items.append({"label": "Volatilitas (ATR)", "value": volatility_delta, "type": "bullish"})
    if news_delta:
        items.append({
            "label": "Sentimen berita",
            "value": news_delta,
            "type": "bullish" if news_delta > 0 else "bearish",
        })

    return {
        "items": items,
        "total": final_score,
        "methodology": SCORE_METHODOLOGY,
    }


def determine_action(
    score: int,
    signals: list[dict],
    liquidity_ok: bool,
    params: TradingParams | None = None,
) -> tuple[str, str | None]:
    p = params or DEFAULT_PARAMS
    bullish = [s for s in signals if s["type"] == "bullish"]
    bearish = [s for s in signals if s["type"] == "bearish"]

    has_trend = any(s["name"] in TREND_BULLISH for s in bullish)
    has_downtrend = any(s["name"] in TREND_BEARISH for s in bearish)

    if not liquidity_ok:
        return "HOLD", f"Likuiditas rendah (< Rp {p.min_daily_turnover / 1e9:.0f} M/hari)"

    if score >= p.min_buy_score and len(bullish) >= p.min_bullish_signals and has_trend:
        return "BUY", None

    if score <= p.min_sell_score and len(bearish) >= p.min_bearish_signals and has_downtrend:
        return "SELL", None

    return "HOLD", None
