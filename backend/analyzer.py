from data_fetcher import fetch_chart
from indicators import compute_all
from idx_stocks import normalize_ticker
from trade_plan import calculate_trade_plan
from news_fetcher import fetch_news
from news_sentiment import analyze_news_sentiment, news_score_adjustment
from scoring import (
    MIN_DAILY_TURNOVER_IDR,
    avg_daily_turnover,
    build_score_breakdown,
    determine_action,
    SCORE_METHODOLOGY,
)


def latest_signals(row: dict, prev: dict) -> list[dict]:
    signals = []

    rsi = row.get("rsi")
    if rsi is not None:
        if rsi < 30:
            signals.append({"name": "RSI Oversold", "type": "bullish", "value": round(rsi, 1)})
        elif rsi > 70:
            signals.append({"name": "RSI Overbought", "type": "bearish", "value": round(rsi, 1)})

    if row.get("macd") is not None and prev.get("macd") is not None:
        if prev["macd"] <= prev["macd_signal"] and row["macd"] > row["macd_signal"]:
            signals.append({"name": "MACD Bullish Cross", "type": "bullish", "value": round(row["macd_hist"], 4)})
        elif prev["macd"] >= prev["macd_signal"] and row["macd"] < row["macd_signal"]:
            signals.append({"name": "MACD Bearish Cross", "type": "bearish", "value": round(row["macd_hist"], 4)})

    if row.get("ema9") is not None and row.get("ema21") is not None:
        if row["close"] > row["ema9"] > row["ema21"]:
            signals.append({"name": "Price Above EMA9/21", "type": "bullish", "value": None})
        elif row["close"] < row["ema9"] < row["ema21"]:
            signals.append({"name": "Price Below EMA9/21", "type": "bearish", "value": None})

    rel_vol = row.get("rel_volume")
    if rel_vol is not None and rel_vol > 1.5:
        signals.append({"name": "Volume Spike", "type": "bullish", "value": round(rel_vol, 2)})

    if row.get("bb_upper") is not None and row.get("bb_lower") is not None:
        if row["close"] <= row["bb_lower"]:
            signals.append({"name": "At Lower Bollinger", "type": "bullish", "value": None})
        elif row["close"] >= row["bb_upper"]:
            signals.append({"name": "At Upper Bollinger", "type": "bearish", "value": None})

    return signals


def score_stock(signals: list[dict], row: dict, prev: dict) -> tuple[int, list[str], int, int]:
    score = 50
    reasons = []
    momentum_delta = 0
    volatility_delta = 0

    for sig in signals:
        if sig["type"] == "bullish":
            score += 6
            reasons.append(f"+ {sig['name']}")
        elif sig["type"] == "bearish":
            score -= 6
            reasons.append(f"- {sig['name']}")

    change_pct = 0.0
    if prev["close"] != 0:
        change_pct = ((row["close"] - prev["close"]) / prev["close"]) * 100

    if change_pct > 2:
        score += 5
        momentum_delta = 5
        reasons.append(f"+ Momentum naik {change_pct:.1f}%")
    elif change_pct < -2:
        score -= 5
        momentum_delta = -5
        reasons.append(f"- Momentum turun {change_pct:.1f}%")

    if row.get("atr") and row["close"] != 0:
        atr_pct = (row["atr"] / row["close"]) * 100
        if atr_pct > 3:
            score += 5
            volatility_delta = 5
            reasons.append(f"+ Volatilitas tinggi (ATR {atr_pct:.1f}%)")

    score = max(0, min(100, score))
    return score, reasons, momentum_delta, volatility_delta


def analyze_ticker(ticker: str) -> dict | None:
    try:
        ticker = normalize_ticker(ticker)
        bars, meta = fetch_chart(ticker)
        if len(bars) < 30:
            return None

        enriched = compute_all(bars)
        row = enriched[-1]
        prev = enriched[-2]
        signals = latest_signals(row, prev)
        score, reasons, momentum_delta, volatility_delta = score_stock(signals, row, prev)

        turnover = row["close"] * row["volume"]
        avg_turnover = avg_daily_turnover(enriched)
        liquidity_ok = avg_turnover >= MIN_DAILY_TURNOVER_IDR

        code = ticker.replace(".JK", "")
        headlines = fetch_news(ticker, code)
        sentiment = analyze_news_sentiment(headlines)
        news_delta, news_reasons, news_signals = news_score_adjustment(sentiment)
        reasons = reasons + news_reasons
        signals = signals + news_signals

        if news_delta != 0:
            score = max(0, min(100, score + news_delta))

        action, action_note = determine_action(score, signals, liquidity_ok)
        if action_note:
            reasons.append(f"○ {action_note}")

        change_pct = ((row["close"] - prev["close"]) / prev["close"]) * 100
        trade_plan = calculate_trade_plan(action, row, enriched)
        sparkline = [round(b["close"], 2) for b in enriched[-10:]]

        return {
            "code": code,
            "ticker": ticker,
            "name": meta["name"],
            "price": round(row["close"], 2),
            "change_pct": round(change_pct, 2),
            "volume": int(row["volume"]),
            "turnover": round(turnover, 0),
            "avg_turnover": round(avg_turnover, 0),
            "liquidity_ok": liquidity_ok,
            "rel_volume": round(row["rel_volume"], 2) if row["rel_volume"] else None,
            "rsi": round(row["rsi"], 1) if row["rsi"] is not None else None,
            "macd_hist": round(row["macd_hist"], 4) if row["macd_hist"] is not None else None,
            "atr_pct": round(row["atr"] / row["close"] * 100, 2) if row.get("atr") else None,
            "score": score,
            "score_breakdown": build_score_breakdown(
                signals, momentum_delta, volatility_delta, news_delta, score
            ),
            "action": action,
            "signals": signals,
            "reasons": reasons,
            "sparkline": sparkline,
            "currency": meta["currency"],
            "trade_plan": trade_plan,
            "news_sentiment": sentiment["score"],
            "news_label": sentiment["label"],
            "news": {
                "sentiment": sentiment,
                "headlines": headlines[:5],
            },
        }
    except Exception:
        return None


def get_score_methodology() -> dict:
    return SCORE_METHODOLOGY
