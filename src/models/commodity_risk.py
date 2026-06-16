import statistics
from datetime import datetime, timedelta

from src.data.commodity_prices import get_commodity_prices, INDUSTRY_COMMODITIES


def _filter_to_window(history, days):
    """Filters price history down to entries within the last `days` calendar days.

    This matters because Copper, Aluminum, Wheat, Corn, and Cotton only have monthly
    data on Alpha Vantage's free tier. Taking 'the last 90 entries' for those would
    actually span 7+ years, not 90 days. Filtering by real calendar date keeps the
    math honest, even though it means very few points for monthly commodities.
    """
    cutoff = datetime.now() - timedelta(days=days)
    return [item for item in history if datetime.strptime(item["date"], "%Y-%m-%d") >= cutoff]


def calculate_trend_score(prices, days=90):
    """0-100: how much has the price risen (or fallen) in the given window.
    +30% change -> 100 (high risk). -10% change -> 0 (low risk, prices easing).
    """
    windowed = _filter_to_window(prices, days)
    if len(windowed) < 2:
        # Monthly commodities can have too few points in a 90-day window.
        # Fall back to the oldest/newest points we actually have rather than failing.
        windowed = prices[-2:] if len(prices) >= 2 else prices
    if len(windowed) < 2:
        return 50  # Can't compute a trend from a single point - treat as unknown/moderate

    old_price, recent_price = windowed[0]["value"], windowed[-1]["value"]
    pct_change = (recent_price - old_price) / old_price
    score = (pct_change + 0.10) / 0.40 * 100
    return max(0, min(100, score))


def calculate_volatility_score(prices, days=90):
    """0-100: how much the price has been swinging, via coefficient of variation.
    CV of 0.20 (20% swings) -> 100 (very volatile). CV of 0 -> 0 (stable).
    """
    windowed = _filter_to_window(prices, days)
    if len(windowed) < 3:
        windowed = prices[-6:] if len(prices) >= 6 else prices
    values = [item["value"] for item in windowed]
    if len(values) < 3:
        return 30  # Too few points to measure volatility meaningfully - assume low-moderate

    mean_price = statistics.mean(values)
    cv = statistics.stdev(values) / mean_price if mean_price else 0
    score = (cv / 0.20) * 100
    return max(0, min(100, score))


def calculate_commodity_risk(industry):
    """Returns the overall commodity risk score plus a per-commodity breakdown,
    so the dashboard can show both the headline number and what's driving it.
    """
    if industry not in INDUSTRY_COMMODITIES:
        raise ValueError(f"Unknown industry: {industry}")

    price_data = get_commodity_prices(industry)

    by_commodity = {}
    for name, history in price_data.items():
        trend = calculate_trend_score(history)
        volatility = calculate_volatility_score(history)
        by_commodity[name] = {
            "trend": round(trend, 1),
            "volatility": round(volatility, 1),
            "combined": round(trend * 0.6 + volatility * 0.4, 1),
        }

    overall = sum(c["combined"] for c in by_commodity.values()) / len(by_commodity)
    return {"score": round(overall, 1), "by_commodity": by_commodity}


if __name__ == "__main__":
    for industry in INDUSTRY_COMMODITIES:
        result = calculate_commodity_risk(industry)
        print(f"\n=== {industry}: Commodity Risk = {result['score']} ===")
        for name, scores in result["by_commodity"].items():
            print(f"  {name}: trend={scores['trend']} volatility={scores['volatility']} combined={scores['combined']}")
