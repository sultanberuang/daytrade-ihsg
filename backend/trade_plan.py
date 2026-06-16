def round_idx_price(price: float) -> float:
    if price >= 5000:
        return round(price / 25) * 25
    if price >= 2000:
        return round(price / 10) * 10
    if price >= 500:
        return round(price / 5) * 5
    return round(price)


def calculate_trade_plan(action: str, row: dict, enriched: list[dict]) -> dict:
    price = row["close"]
    atr = row.get("atr") or price * 0.02

    recent = enriched[-5:]
    swing_low = min(b["low"] for b in recent)
    swing_high = max(b["high"] for b in recent)
    bb_upper = row.get("bb_upper")
    bb_lower = row.get("bb_lower")
    ema9 = row.get("ema9")

    if action == "BUY":
        entry = ema9 if ema9 and ema9 < price else price
        sl_atr = price - 1.5 * atr
        sl = max(sl_atr, swing_low * 0.998)
        if bb_lower and bb_lower < price:
            sl = max(sl, bb_lower * 0.998)

        tp1 = price + 1.5 * atr
        tp2 = price + 2.5 * atr
        if bb_upper and bb_upper > price:
            tp2 = min(tp2, bb_upper)

        risk = entry - sl
        reward = tp1 - entry
        rr = round(reward / risk, 2) if risk > 0 else None

        return _plan(
            side="long",
            entry=entry,
            sl=sl,
            tp1=tp1,
            tp2=tp2,
            rr=rr,
            note="Entry long, SL di bawah swing low / 1.5×ATR",
        )

    if action == "SELL":
        entry = ema9 if ema9 and ema9 > price else price
        sl_atr = price + 1.5 * atr
        sl = min(sl_atr, swing_high * 1.002)
        if bb_upper and bb_upper > price:
            sl = min(sl, bb_upper * 1.002)

        tp1 = price - 1.5 * atr
        tp2 = price - 2.5 * atr
        if bb_lower and bb_lower < price:
            tp2 = max(tp2, bb_lower)

        risk = sl - entry
        reward = entry - tp1
        rr = round(reward / risk, 2) if risk > 0 else None

        return _plan(
            side="short",
            entry=entry,
            sl=sl,
            tp1=tp1,
            tp2=tp2,
            rr=rr,
            note="Entry short/jual, SL di atas swing high / 1.5×ATR",
        )

    # HOLD — level referensi konservatif
    sl = price - 1.0 * atr
    tp1 = price + 1.0 * atr
    return _plan(
        side="neutral",
        entry=price,
        sl=sl,
        tp1=tp1,
        tp2=price + 2.0 * atr,
        rr=None,
        note="Hold — level referensi saja, tunggu konfirmasi sinyal",
    )


def _plan(side: str, entry: float, sl: float, tp1: float, tp2: float, rr: float | None, note: str) -> dict:
    entry_r = round_idx_price(entry)
    sl_r = round_idx_price(sl)
    tp1_r = round_idx_price(tp1)
    tp2_r = round_idx_price(tp2)

    risk_abs = abs(entry_r - sl_r)
    reward_abs = abs(tp1_r - entry_r)

    return {
        "side": side,
        "entry": entry_r,
        "sl": sl_r,
        "tp1": tp1_r,
        "tp2": tp2_r,
        "risk_reward": rr,
        "risk_pct": round(risk_abs / entry_r * 100, 2) if entry_r else None,
        "reward_pct": round(reward_abs / entry_r * 100, 2) if entry_r else None,
        "risk_amount": round(risk_abs, 0),
        "reward_amount": round(reward_abs, 0),
        "note": note,
    }
