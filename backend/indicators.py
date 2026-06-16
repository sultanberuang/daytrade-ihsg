def ema(values: list[float], period: int) -> list[float | None]:
    if len(values) < period:
        return [None] * len(values)
    k = 2 / (period + 1)
    result: list[float | None] = [None] * (period - 1)
    sma = sum(values[:period]) / period
    result.append(sma)
    prev = sma
    for v in values[period:]:
        prev = v * k + prev * (1 - k)
        result.append(prev)
    return result


def sma(values: list[float], period: int) -> list[float | None]:
    result: list[float | None] = [None] * len(values)
    for i in range(period - 1, len(values)):
        result[i] = sum(values[i - period + 1 : i + 1]) / period
    return result


def rsi(closes: list[float], period: int = 14) -> list[float | None]:
    if len(closes) < period + 1:
        return [None] * len(closes)

    gains, losses = [], []
    for i in range(1, len(closes)):
        diff = closes[i] - closes[i - 1]
        gains.append(max(diff, 0))
        losses.append(max(-diff, 0))

    result: list[float | None] = [None] * period
    avg_gain = sum(gains[:period]) / period
    avg_loss = sum(losses[:period]) / period

    if avg_loss == 0:
        result.append(100.0)
    else:
        rs = avg_gain / avg_loss
        result.append(100 - (100 / (1 + rs)))

    for i in range(period, len(gains)):
        avg_gain = (avg_gain * (period - 1) + gains[i]) / period
        avg_loss = (avg_loss * (period - 1) + losses[i]) / period
        if avg_loss == 0:
            result.append(100.0)
        else:
            rs = avg_gain / avg_loss
            result.append(100 - (100 / (1 + rs)))

    return result


def macd(closes: list[float], fast: int = 12, slow: int = 26, signal: int = 9):
    ema_fast = ema(closes, fast)
    ema_slow = ema(closes, slow)
    macd_line: list[float | None] = [None] * len(closes)
    for i in range(len(closes)):
        if ema_fast[i] is not None and ema_slow[i] is not None:
            macd_line[i] = ema_fast[i] - ema_slow[i]

    valid_macd = [v if v is not None else 0.0 for v in macd_line]
    signal_line_raw = ema(valid_macd, signal)
    signal_line: list[float | None] = []
    for i, m in enumerate(macd_line):
        if m is None:
            signal_line.append(None)
        else:
            signal_line.append(signal_line_raw[i])

    hist: list[float | None] = []
    for m, s in zip(macd_line, signal_line):
        hist.append(m - s if m is not None and s is not None else None)

    return macd_line, signal_line, hist


def bollinger(closes: list[float], period: int = 20, std_dev: float = 2.0):
    mid = sma(closes, period)
    upper: list[float | None] = [None] * len(closes)
    lower: list[float | None] = [None] * len(closes)
    for i in range(period - 1, len(closes)):
        window = closes[i - period + 1 : i + 1]
        mean = mid[i]
        if mean is None:
            continue
        variance = sum((x - mean) ** 2 for x in window) / period
        sd = variance ** 0.5
        upper[i] = mean + std_dev * sd
        lower[i] = mean - std_dev * sd
    return upper, lower


def atr(highs: list[float], lows: list[float], closes: list[float], period: int = 14) -> list[float | None]:
    trs = [highs[0] - lows[0]]
    for i in range(1, len(closes)):
        tr = max(
            highs[i] - lows[i],
            abs(highs[i] - closes[i - 1]),
            abs(lows[i] - closes[i - 1]),
        )
        trs.append(tr)
    return sma(trs, period)


def compute_all(bars: list[dict]) -> list[dict]:
    closes = [b["close"] for b in bars]
    highs = [b["high"] for b in bars]
    lows = [b["low"] for b in bars]
    volumes = [b["volume"] for b in bars]

    rsi_vals = rsi(closes)
    macd_line, macd_signal, macd_hist = macd(closes)
    ema9 = ema(closes, 9)
    ema21 = ema(closes, 21)
    bb_upper, bb_lower = bollinger(closes)
    atr_vals = atr(highs, lows, closes)
    vol_sma20 = sma(volumes, 20)

    enriched = []
    for i, bar in enumerate(bars):
        rel_vol = None
        if vol_sma20[i] and vol_sma20[i] > 0:
            rel_vol = volumes[i] / vol_sma20[i]
        enriched.append({
            **bar,
            "rsi": rsi_vals[i],
            "macd": macd_line[i],
            "macd_signal": macd_signal[i],
            "macd_hist": macd_hist[i],
            "ema9": ema9[i],
            "ema21": ema21[i],
            "bb_upper": bb_upper[i],
            "bb_lower": bb_lower[i],
            "atr": atr_vals[i],
            "rel_volume": rel_vol,
        })
    return enriched
