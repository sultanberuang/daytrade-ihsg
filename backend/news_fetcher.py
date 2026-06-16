import xml.etree.ElementTree as ET
from datetime import datetime, timezone, timedelta
import httpx

YAHOO_RSS = "https://feeds.finance.yahoo.com/rss/2.0/headline?s={symbol}&region=ID&lang=id-ID"
GOOGLE_RSS = "https://news.google.com/rss/search?q={query}&hl=id&gl=ID&ceid=ID:id"
HEADERS = {"User-Agent": "Mozilla/5.0"}
CACHE_TTL = timedelta(hours=1)
_cache: dict[str, tuple[datetime, list[dict]]] = {}


def _parse_rss(xml_text: str, source: str) -> list[dict]:
    items = []
    try:
        root = ET.fromstring(xml_text)
        for item in root.findall(".//item"):
            title = item.findtext("title") or ""
            link = item.findtext("link") or ""
            pub = item.findtext("pubDate") or ""
            if title.strip():
                items.append({"title": title.strip(), "link": link, "published": pub, "source": source})
    except ET.ParseError:
        pass
    return items


def fetch_news(ticker: str, code: str | None = None) -> list[dict]:
    symbol = ticker if ticker.endswith(".JK") else f"{ticker}.JK"
    code = code or symbol.replace(".JK", "")

    cached = _cache.get(symbol)
    if cached and datetime.now(timezone.utc) - cached[0] < CACHE_TTL:
        return cached[1]

    news: list[dict] = []
    queries = [
        (YAHOO_RSS.format(symbol=symbol), "Yahoo Finance"),
        (GOOGLE_RSS.format(query=f"{code}+saham+IDX"), "Google News"),
    ]

    with httpx.Client(timeout=4.0, headers=HEADERS, follow_redirects=True) as client:
        for url, source in queries:
            try:
                resp = client.get(url)
                if resp.status_code == 200:
                    news.extend(_parse_rss(resp.text, source))
            except Exception:
                continue

    seen = set()
    unique = []
    for item in news:
        key = item["title"].lower()
        if key not in seen:
            seen.add(key)
            unique.append(item)

    unique = unique[:8]
    _cache[symbol] = (datetime.now(timezone.utc), unique)
    return unique
