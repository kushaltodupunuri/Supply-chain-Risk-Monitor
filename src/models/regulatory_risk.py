from src.data.news_alerts import get_industry_alert, REGULATORY_KEYWORDS

# Hand-curated baseline reflecting known, current trade/regulatory exposure per
# industry - same approach as shipping.py's manually curated route status, since
# there's no free API that publishes a continuously-updated "regulatory risk index"
# per industry. Update every few weeks as real trade policy news develops.
# Last updated: 2026-06-16
REGULATORY_BASELINE = {
    "Electronics": {
        "base_score": 55,
        "summary": "Ongoing US-China semiconductor export controls and tariffs on chip-related goods",
    },
    "Automotive": {
        "base_score": 50,
        "summary": "EV tariffs and steel/aluminum tariffs continue to affect cross-border auto supply chains",
    },
    "Pharma": {
        "base_score": 30,
        "summary": "Relatively stable trade environment for pharmaceutical imports/exports currently",
    },
    "Retail": {
        "base_score": 50,
        "summary": "Apparel and consumer goods tariffs affecting China-sourced retail goods",
    },
    "Food & Beverage": {
        "base_score": 40,
        "summary": "Agricultural trade tensions and periodic grain export restrictions in key exporting nations",
    },
}


def calculate_regulatory_risk(industry, use_news_alerts=True):
    """Returns a 0-100 regulatory/trade-policy risk score: a hand-curated baseline
    (slow-moving, since trade policy doesn't shift daily) plus a live news-spike
    layer watching for sudden tariff/trade-policy headlines - same two-layer pattern
    used for logistics_risk.py and geopolitical_risk.py.
    """
    if industry not in REGULATORY_BASELINE:
        raise ValueError(f"Unknown industry: {industry}")

    baseline = REGULATORY_BASELINE[industry]
    alert_adjustment = 0
    if use_news_alerts:
        try:
            alert_adjustment = get_industry_alert(industry, REGULATORY_KEYWORDS, "regulatory")["adjustment"]
        except Exception:
            alert_adjustment = 0  # NewsAPI hiccup shouldn't break the whole score

    final_score = min(100, baseline["base_score"] + alert_adjustment)
    return {
        "score": round(final_score, 1),
        "base": baseline["base_score"],
        "alert_adjustment": alert_adjustment,
        "summary": baseline["summary"],
    }


if __name__ == "__main__":
    for industry in REGULATORY_BASELINE:
        result = calculate_regulatory_risk(industry)
        print(f"{industry}: {result['score']} (base={result['base']}, alert=+{result['alert_adjustment']})")
        print(f"  {result['summary']}")
