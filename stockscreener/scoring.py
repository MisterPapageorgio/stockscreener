from __future__ import annotations

import numpy as np
import pandas as pd


def _scale(value: pd.Series, low: float, high: float) -> pd.Series:
    return ((value - low) / (high - low)).clip(0, 1) * 100


def technical_features(prices: pd.DataFrame, benchmark: pd.Series) -> pd.DataFrame:
    rows = []
    for ticker, frame in prices.groupby("ticker"):
        frame = frame.sort_values("date").set_index("date")
        close = frame["adjusted_close"].astype(float)
        returns = close.pct_change()
        latest = close.iloc[-1]
        high_52w = close.tail(252).max()
        ret_5d = close.pct_change(5).iloc[-1]
        ret_20d = close.pct_change(20).iloc[-1]
        ret_6m = close.pct_change(126).iloc[-1]
        benchmark_5d = benchmark.pct_change(5).iloc[-1]
        benchmark_20d = benchmark.pct_change(20).iloc[-1]
        benchmark_6m = benchmark.pct_change(126).iloc[-1]
        vol = returns.tail(60).std() * np.sqrt(252)
        downside_return = min(ret_5d - benchmark_5d, 0)
        shock = -downside_return / max(vol / np.sqrt(12), 0.01)
        volume_ratio = frame.volume.iloc[-1] / max(frame.volume.tail(20).mean(), 1)
        rows.append({
            "ticker": ticker, "as_of": frame.index[-1], "price": latest,
            "price_change_5d": ret_5d, "price_change_20d": ret_20d,
            "price_change_6m": ret_6m,
            "relative_return_5d": ret_5d - benchmark_5d,
            "relative_return_20d": ret_20d - benchmark_20d,
            "relative_return_6m": ret_6m - benchmark_6m,
            "drawdown_52w": latest / high_52w - 1, "volatility_60d": vol,
            "volume_ratio": volume_ratio, "shock": shock,
        })
    return pd.DataFrame(rows)


def add_sector_trends(result: pd.DataFrame) -> pd.DataFrame:
    enriched = result.copy()
    relative_return = enriched.get("relative_return_20d", enriched["price_change_20d"])
    sector_stats = enriched.assign(_sector_relative_return=relative_return).groupby("sector").agg(
        sector_relative_return=("_sector_relative_return", "median"),
        sector_positive_breadth=("_sector_relative_return", lambda values: (values > 0).mean()),
    )

    def classify(row: pd.Series) -> str:
        performance = row.sector_relative_return
        breadth = row.sector_positive_breadth
        if performance >= 0.08 and breadth >= 0.65:
            return "Überhitzt"
        if performance >= 0.03 and breadth >= 0.55:
            return "Stark"
        if performance <= -0.08 and breadth <= 0.40:
            return "Geschwächt"
        if performance <= -0.03 and breadth <= 0.45:
            return "Schwach"
        return "Neutral"

    enriched["sector_trend"] = enriched["sector"].map(sector_stats.apply(classify, axis=1))

    if "relative_return_6m" not in enriched.columns:
        enriched["sector_trend_6m"] = "Nach Scan verfügbar"
        return enriched

    long_stats = enriched.groupby("sector").agg(
        sector_relative_return=("relative_return_6m", "median"),
        sector_positive_breadth=("relative_return_6m", lambda values: (values > 0).mean()),
    )

    def classify_long(row: pd.Series) -> str:
        performance = row.sector_relative_return
        breadth = row.sector_positive_breadth
        if performance >= 0.15 and breadth >= 0.65:
            return "Überhitzt"
        if performance >= 0.06 and breadth >= 0.55:
            return "Stark"
        if performance <= -0.15 and breadth <= 0.40:
            return "Geschwächt"
        if performance <= -0.06 and breadth <= 0.45:
            return "Schwach"
        return "Neutral"

    enriched["sector_trend_6m"] = enriched["sector"].map(long_stats.apply(classify_long, axis=1))
    return enriched


def score_signals(features: pd.DataFrame, fundamentals: pd.DataFrame) -> pd.DataFrame:
    result = features.merge(fundamentals, on="ticker", how="left").fillna(0)
    result["dip_score"] = (
        _scale(-result.relative_return_5d, 0, 0.20) * 0.15
        + _scale(result.shock, 0, 6) * 0.10
        + _scale(-result.price_change_20d, 0, 0.35) * 0.30
        + _scale(result.volume_ratio - 1, 0, 3) * 0.05
        + _scale(-result.drawdown_52w, 0, 0.50) * 0.40
    )
    result["quality_score"] = (
        _scale(result.revenue_growth, -0.10, 0.30) * 0.15
        + _scale(result.eps_growth, -0.20, 0.40) * 0.15
        + _scale(result.fcf_growth, -0.20, 0.40) * 0.15
        + _scale(result.roic, 0, 0.40) * 0.20
        + _scale(result.fcf_margin, 0, 0.35) * 0.20
        + _scale(result.operating_margin, 0, 0.40) * 0.15
    )
    result["valuation_score"] = (
        _scale(result.fcf_yield, 0, 0.12) * 0.45
        + _scale(-result.pe_discount, 0, 0.50) * 0.25
        + _scale(-result.ev_ebit_discount, 0, 0.50) * 0.20
        + _scale(result.peg_discount, 0, 0.50) * 0.10
    )
    result["overall_score"] = result.quality_score * 0.45 + result.valuation_score * 0.20 + result.dip_score * 0.35
    result["reason"] = result.apply(lambda row: (
        f"{row.price_change_5d:.1%} in 5 Tagen, relativ zum NDX {row.relative_return_5d:.1%}; "
        f"Volumen {row.volume_ratio:.1f}x normal. FCF-Marge {row.fcf_margin:.1%}, "
        f"FCF-Yield {row.fcf_yield:.1%}."
    ), axis=1)
    return result.sort_values("overall_score", ascending=False)
