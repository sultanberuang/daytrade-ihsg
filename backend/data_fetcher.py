import httpx

YAHOO_CHART = "https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"
HEADERS = {"User-Agent": "Mozilla/5.0"}


def fetch_chart(symbol: str, range_: str = "3mo", interval: str = "1d") -> tuple[list[dict], dict]:
    params = {"range": range_, "interval": interval}
    url = YAHOO_CHART.format(symbol=symbol)

    with httpx.Client(timeout=15.0, headers=HEADERS) as client:
        resp = client.get(url, params=params)
        resp.raise_for_status()
        data = resp.json()

    result = data["chart"]["result"][0]
    meta = result.get("meta", {})
    timestamps = result["timestamp"]
    quote = result["indicators"]["quote"][0]

    bars = []
    for i, ts in enumerate(timestamps):
        close = quote["close"][i]
        if close is None:
            continue
        bars.append({
            "timestamp": ts,
            "open": quote["open"][i],
            "high": quote["high"][i],
            "low": quote["low"][i],
            "close": close,
            "volume": quote["volume"][i] or 0,
        })

    quote_meta = {
        "name": meta.get("shortName") or meta.get("longName") or symbol,
        "currency": meta.get("currency", "IDR"),
    }
    return bars, quote_meta


def fetch_ohlcv(symbol: str, range_: str = "3mo", interval: str = "1d") -> list[dict]:
    bars, _ = fetch_chart(symbol, range_, interval)
    return bars


def fetch_quote_meta(symbol: str) -> dict:
    _, meta = fetch_chart(symbol, range_="1d", interval="1d")
    return meta
