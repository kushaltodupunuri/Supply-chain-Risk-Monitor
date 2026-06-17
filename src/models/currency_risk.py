import statistics
from datetime import datetime, timedelta

from src.data.currency import get_fx_history
from src.models.geopolitical_risk import INDUSTRY_SOURCING_WEIGHTS


def calculate_fx_volatility_score(history, days=90):
    """0-100: how much the exchange rate has been swinging recently. FX is typically
    far less volatile than commodities, so this scale is tighter than commodity_risk's.
    Direction (currency strengthening vs weakening) is intentionally not scored here -
    FRED's quoting convention differs by currency pair (some are "X per USD", others
    "USD per X"), so a single directional rule would be wrong for some currencies.
    Volatility itself is a legitimate, direction-agnostic risk signal: unpredictable
    exchange rates make costs hard to plan for regardless of which way they move.
    """
    if not history:
        return None
    cutoff = datetime.now() - timedelta(days=days)
    windowed = [item for item in history if datetime.strptime(item["date"], "%Y-%m-%d") >= cutoff]
    values = [item["value"] for item in windowed] if len(windowed) >= 3 else [item["value"] for item in history[-10:]]
    if len(values) < 3:
        return None

    mean_rate = statistics.mean(values)
    cv = statistics.stdev(values) / mean_rate if mean_rate else 0
    score = (cv / 0.04) * 100  # CV of 4% -> max risk; major-currency CVs are typically 1-3%
    return max(0, min(100, score))


def calculate_currency_risk(industry):
    """Returns a 0-100 currency/FX risk score weighted by sourcing share, using only
    the countries that have a free FRED exchange rate series available. Countries
    without one (Taiwan, Vietnam, Bangladesh, Argentina, Ukraine, as of this data
    source) are excluded and their weight is redistributed among the countries that
    do have data, rather than guessing a number for them.
    """
    if industry not in INDUSTRY_SOURCING_WEIGHTS:
        raise ValueError(f"Unknown industry: {industry}")

    sourcing = INDUSTRY_SOURCING_WEIGHTS[industry]
    by_country = {}
    for code, weight in sourcing.items():
        score = calculate_fx_volatility_score(get_fx_history(code))
        if score is not None:
            by_country[code] = {"weight": weight, "score": round(score, 1)}

    if not by_country:
        return {"score": 50.0, "by_country": {}}  # No FX data at all for this industry's countries

    total_weight = sum(c["weight"] for c in by_country.values())
    weighted_score = sum(c["score"] * c["weight"] for c in by_country.values()) / total_weight

    return {"score": round(weighted_score, 1), "by_country": by_country}


if __name__ == "__main__":
    for industry in INDUSTRY_SOURCING_WEIGHTS:
        result = calculate_currency_risk(industry)
        print(f"{industry}: {result['score']} (from {len(result['by_country'])} countries with FX data)")
        for code, data in result["by_country"].items():
            print(f"  {code}: weight={data['weight']} score={data['score']}")
