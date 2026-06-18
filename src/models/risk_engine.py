from src.models.supplier_risk import calculate_supplier_risk
from src.models.commodity_risk import calculate_commodity_risk
from src.models.logistics_risk import calculate_logistics_risk
from src.models.geopolitical_risk import calculate_geopolitical_risk
from src.models.regulatory_risk import calculate_regulatory_risk

# Currency/FX and Climate/Disaster risk were tried and then dropped per user feedback.
# Used as the fallback for any industry without its own weight breakdown below -
# supplier concentration as the largest single factor (the most fundamental
# structural risk), with the rest spread across the remaining 4 dimensions.
WEIGHTS = {
    "supplier": 0.25,
    "commodity": 0.20,
    "logistics": 0.20,
    "geopolitical": 0.20,
    "regulatory": 0.15,
}

# Industry-specific weights: how much each of the 5 categories should count toward
# the overall score. Weights shift by industry because the same dimension doesn't
# matter equally everywhere - e.g. supplier concentration is the dominant risk for
# semiconductor-dependent Electronics, but commodity price swings matter more for
# Food & Beverage. Falls back to the flat WEIGHTS above for any industry not yet
# given a specific breakdown.
WEIGHTS_BY_INDUSTRY = {
    "Electronics": {
        "supplier": 0.30,
        "geopolitical": 0.25,
        "commodity": 0.20,
        "logistics": 0.15,
        "regulatory": 0.10,
    },
}


def get_weights(industry):
    return WEIGHTS_BY_INDUSTRY.get(industry, WEIGHTS)


def get_risk_label(score):
    if score <= 30:
        return "Low Risk"
    elif score <= 60:
        return "Moderate Risk"
    elif score <= 80:
        return "High Risk"
    return "Critical Risk"


def calculate_risk_score(industry):
    """Returns the full risk picture for an industry: the overall weighted score,
    each of the 5 sub-scores, and the detailed breakdown behind each one (so the
    dashboard can show both the headline number and what's driving it).
    """
    supplier_score = calculate_supplier_risk(industry)
    commodity_result = calculate_commodity_risk(industry)
    logistics_result = calculate_logistics_risk()
    geopolitical_result = calculate_geopolitical_risk(industry)
    regulatory_result = calculate_regulatory_risk(industry)

    sub_scores = {
        "supplier": supplier_score,
        "commodity": commodity_result["score"],
        "logistics": logistics_result["score"],
        "geopolitical": geopolitical_result["score"],
        "regulatory": regulatory_result["score"],
    }

    weights = get_weights(industry)
    total = sum(sub_scores[key] * weights[key] for key in weights)

    return {
        "industry": industry,
        "total": round(total, 1),
        "label": get_risk_label(total),
        "sub_scores": {key: round(value, 1) for key, value in sub_scores.items()},
        "weights": weights,
        "details": {
            "commodity": commodity_result,
            "logistics": logistics_result,
            "geopolitical": geopolitical_result,
            "regulatory": regulatory_result,
        },
    }


if __name__ == "__main__":
    industries = ["Electronics", "Pharma", "Automotive", "Retail", "Food & Beverage"]
    results = [calculate_risk_score(industry) for industry in industries]

    print("=== Overall Risk Scores (sorted highest to lowest) ===")
    for result in sorted(results, key=lambda r: r["total"], reverse=True):
        s = result["sub_scores"]
        print(f"\n{result['industry']}: {result['total']}/100 ({result['label']})")
        print(f"  Supplier={s['supplier']} | Commodity={s['commodity']} | "
              f"Logistics={s['logistics']} | Geopolitical={s['geopolitical']} | "
              f"Regulatory={s['regulatory']}")
