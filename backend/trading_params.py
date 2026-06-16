"""Parameter trading terpusat — dioptimasi via optimize_params.py (backtest YTD 2026)."""
from dataclasses import dataclass, asdict


@dataclass
class TradingParams:
    min_buy_score: int = 72
    min_bullish_signals: int = 2
    min_sell_score: int = 32
    min_bearish_signals: int = 2
    min_daily_turnover: float = 5_000_000_000
    sl_atr_mult: float = 2.5
    tp1_atr_mult: float = 0.8
    tp2_atr_mult: float = 1.6
    min_risk_reward: float = 1.5
    max_gap_entry_pct: float = 2.0


DEFAULT_PARAMS = TradingParams()

TREND_BULLISH = frozenset({"MACD Bullish Cross", "Price Above EMA9/21", "Volume Spike"})
TREND_BEARISH = frozenset({"MACD Bearish Cross", "Price Below EMA9/21"})


def params_dict(p: TradingParams | None = None) -> dict:
    return asdict(p or DEFAULT_PARAMS)
