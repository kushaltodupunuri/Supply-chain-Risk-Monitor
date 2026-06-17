from src.data.news_alerts import get_industry_alert, CLIMATE_KEYWORDS

# Hand-curated baseline reflecting known climate/disaster exposure of each industry's
# key sourcing regions - same approach as shipping.py, since there's no free,
# continuously-updated "climate risk index" per industry available.
# Last updated: 2026-06-16
CLIMATE_BASELINE = {
    "Electronics": {
        "base_score": 60,
        "summary": "Taiwan (the dominant semiconductor hub) faces earthquake, typhoon, and periodic water-scarcity exposure affecting chip fabrication",
    },
    "Automotive": {
        "base_score": 35,
        "summary": "Diversified manufacturing footprint reduces concentrated climate exposure, though Mexico/Gulf Coast hurricane season is a factor",
    },
    "Pharma": {
        "base_score": 30,
        "summary": "India and China API manufacturing regions face monsoon flooding risk in some production areas",
    },
    "Retail": {
        "base_score": 45,
        "summary": "Bangladesh garment manufacturing faces monsoon flooding and cyclone exposure",
    },
    "Food & Beverage": {
        "base_score": 65,
        "summary": "Direct exposure to droughts and floods affecting crop yields in the US, Brazil, Argentina, and Ukraine - inherently climate-sensitive sourcing",
    },
}


def calculate_climate_risk(industry, use_news_alerts=True):
    """Returns a 0-100 climate/disaster risk score: a hand-curated baseline (slow-
    moving structural exposure) plus a live news-spike layer watching for sudden
    earthquake/flood/hurricane headlines tied to the industry - same two-layer
    pattern used throughout this app.
    """
    if industry not in CLIMATE_BASELINE:
        raise ValueError(f"Unknown industry: {industry}")

    baseline = CLIMATE_BASELINE[industry]
    alert_adjustment = 0
    if use_news_alerts:
        try:
            alert_adjustment = get_industry_alert(industry, CLIMATE_KEYWORDS, "climate")["adjustment"]
        except Exception:
            alert_adjustment = 0

    final_score = min(100, baseline["base_score"] + alert_adjustment)
    return {
        "score": round(final_score, 1),
        "base": baseline["base_score"],
        "alert_adjustment": alert_adjustment,
        "summary": baseline["summary"],
    }


if __name__ == "__main__":
    for industry in CLIMATE_BASELINE:
        result = calculate_climate_risk(industry)
        print(f"{industry}: {result['score']} (base={result['base']}, alert=+{result['alert_adjustment']})")
        print(f"  {result['summary']}")
