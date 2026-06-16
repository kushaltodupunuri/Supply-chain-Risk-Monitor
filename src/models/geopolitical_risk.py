from src.data.geopolitical import get_country_risk, COUNTRY_NAMES
from src.data.news_alerts import get_country_alert

# How much of each industry's sourcing comes from each country. These are modeling
# weights (a judgment call), separate from geopolitical.py's plain country list, and
# should sum to 1.0 per industry.
INDUSTRY_SOURCING_WEIGHTS = {
    "Electronics": {"TW": 0.40, "CN": 0.30, "KR": 0.15, "VN": 0.10, "MY": 0.05},
    "Pharma": {"CN": 0.40, "IN": 0.30, "IE": 0.15, "SG": 0.15},
    "Automotive": {"CN": 0.30, "MX": 0.25, "JP": 0.20, "DE": 0.15, "KR": 0.10},
    "Retail": {"CN": 0.45, "BD": 0.20, "VN": 0.20, "IN": 0.15},
    "Food & Beverage": {"US": 0.30, "BR": 0.25, "AR": 0.15, "AU": 0.15, "UA": 0.15},
}


def wb_score_to_risk(wb_score):
    """Converts a World Bank political stability score (-2.5 worst, +2.5 best) into
    a 0-100 risk score (100 = least stable)."""
    risk = ((wb_score * -1) + 2.5) / 5.0 * 100
    return max(0, min(100, risk))


def calculate_geopolitical_risk(industry, use_news_alerts=True):
    """Returns the overall geopolitical risk score for an industry, weighted by how
    much of its sourcing comes from each country, plus a per-country breakdown.

    Combines the slow World Bank baseline (annual, cached 7 days) with the fast
    news-spike layer (daily, cached 24h) - same two-layer pattern as logistics_risk.py.
    """
    if industry not in INDUSTRY_SOURCING_WEIGHTS:
        raise ValueError(f"Unknown industry: {industry}")

    sourcing = INDUSTRY_SOURCING_WEIGHTS[industry]
    total_score = 0
    by_country = {}

    for code, weight in sourcing.items():
        wb_data = get_country_risk(code)
        base_risk = wb_score_to_risk(wb_data["value"])

        alert_adjustment = 0
        if use_news_alerts:
            try:
                country_name = COUNTRY_NAMES.get(code, code)
                alert_adjustment = get_country_alert(country_name)["adjustment"]
            except Exception:
                alert_adjustment = 0  # NewsAPI hiccup shouldn't break the whole score

        final_risk = min(100, base_risk + alert_adjustment)
        by_country[code] = {
            "name": COUNTRY_NAMES.get(code, code),
            "weight": weight,
            "base": round(base_risk, 1),
            "alert_adjustment": alert_adjustment,
            "final": round(final_risk, 1),
        }
        total_score += final_risk * weight

    return {"score": round(total_score, 1), "by_country": by_country}


if __name__ == "__main__":
    for industry in INDUSTRY_SOURCING_WEIGHTS:
        result = calculate_geopolitical_risk(industry)
        print(f"\n=== {industry}: Geopolitical Risk = {result['score']} ===")
        for code, data in result["by_country"].items():
            print(f"  {data['name']} ({code}, weight={data['weight']}): "
                  f"base={data['base']} alert=+{data['alert_adjustment']} final={data['final']}")
