POSITIVE = [
    "naik", "meroket", "profit", "laba", "untung", "dividen", "ekspansi", "rebound",
    "bullish", "upgrade", "beat", "surge", "gain", "rise", "rally", "strong",
    "growth", "record", "outperform", "buy", "beli", "positif", "optimis",
    "capai", "target", "tinggi", "menguat", "pemulihan", "ekspansi",
]

NEGATIVE = [
    "turun", "anjlok", "rugi", "loss", "bearish", "downgrade", "decline", "drop",
    "fall", "crash", "weak", "suspend", "skandal", "fraud", "default", "boncos",
    "jual", "sell", "negatif", "pesimis", "tekanan", "resesi", "korupsi",
    "penurunan", "merosot", "lemah", "warning", "risiko", "gagal",
]


def analyze_news_sentiment(headlines: list[dict]) -> dict:
    if not headlines:
        return {
            "score": 0,
            "label": "neutral",
            "positive_count": 0,
            "negative_count": 0,
            "headline_count": 0,
        }

    positive = 0
    negative = 0

    for item in headlines:
        text = item.get("title", "").lower()
        pos_hits = sum(1 for w in POSITIVE if w in text)
        neg_hits = sum(1 for w in NEGATIVE if w in text)
        positive += pos_hits
        negative += neg_hits

    total = positive + negative
    if total == 0:
        raw = 0.0
        label = "neutral"
    else:
        raw = (positive - negative) / total
        if raw >= 0.35:
            label = "bullish"
        elif raw <= -0.35:
            label = "bearish"
        else:
            label = "neutral"

    return {
        "score": round(raw, 2),
        "label": label,
        "positive_count": positive,
        "negative_count": negative,
        "headline_count": len(headlines),
    }


def news_score_adjustment(sentiment: dict) -> tuple[int, list[str], list[dict]]:
    """Returns score delta, reasons, and signal entries."""
    score_delta = 0
    reasons = []
    signals = []

    raw = sentiment["score"]
    label = sentiment["label"]
    count = sentiment["headline_count"]

    if count == 0:
        return 0, reasons, signals

    if label == "bullish":
        score_delta = min(10, 5 + int(raw * 5))
        reasons.append(f"+ Berita positif ({count} headline, sentimen {label})")
        signals.append({"name": "News Bullish", "type": "bullish", "value": raw})
    elif label == "bearish":
        score_delta = -min(10, 5 + int(abs(raw) * 5))
        reasons.append(f"- Berita negatif ({count} headline, sentimen {label})")
        signals.append({"name": "News Bearish", "type": "bearish", "value": raw})
    else:
        reasons.append(f"○ Berita netral ({count} headline)")

    return score_delta, reasons, signals
