import json
from pathlib import Path

DATA_FILE = Path(__file__).parent / "data" / "ihsg_tickers.json"
REMOTE_URL = "https://raw.githubusercontent.com/sukirman1901/Pulse-CLI/main/data/tickers.json"


def _load_file() -> dict:
    with open(DATA_FILE, encoding="utf-8") as f:
        return json.load(f)


def get_all_stocks() -> list[dict]:
    data = _load_file()
    return data["stocks"]


def get_all_tickers() -> list[str]:
    return [s["ticker"] for s in get_all_stocks()]


def get_ticker_codes() -> list[str]:
    return [s["code"] for s in get_all_stocks()]


def normalize_ticker(code: str) -> str:
    code = code.upper().strip()
    if code.endswith(".JK"):
        return code
    return f"{code}.JK"


def refresh_from_remote() -> int:
    import httpx

    resp = httpx.get(REMOTE_URL, headers={"User-Agent": "Mozilla/5.0"}, timeout=30)
    resp.raise_for_status()
    codes = sorted(resp.json())
    data = {
        "source": "IHSG",
        "count": len(codes),
        "updated": "remote",
        "stocks": [{"code": c, "ticker": f"{c}.JK"} for c in codes],
    }
    DATA_FILE.parent.mkdir(exist_ok=True)
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    return len(codes)
