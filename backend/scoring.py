MIN_DAILY_TURNOVER_IDR = 5_000_000_000  # Rp 5 Miliar

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
        "Skor ≥ 75",
        "Min. 2 sinyal bullish",
        "Konfirmasi tren (MACD cross / harga > EMA9/21)",
        "Nilai transaksi rata-rata ≥ Rp 5 M/hari",
    ],
    "sell_requirements": [
        "Skor ≤ 32",
        "Min. 2 sinyal bearish",
    ],
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
) -> tuple[str, str | None]:
    bullish = [s for s in signals if s["type"] == "bullish"]
    bearish = [s for s in signals if s["type"] == "bearish"]

    has_trend = any(
        s["name"] in ("MACD Bullish Cross", "Price Above EMA9/21", "Volume Spike")
        for s in bullish
    )
    has_downtrend = any(
        s["name"] in ("MACD Bearish Cross", "Price Below EMA9/21")
        for s in bearish
    )

    if not liquidity_ok:
        return "HOLD", "Likuiditas rendah (< Rp 5M/hari)"

    if score >= 75 and len(bullish) >= 2 and has_trend:
        return "BUY", None

    if score <= 32 and len(bearish) >= 2 and has_downtrend:
        return "SELL", None

    return "HOLD", None
