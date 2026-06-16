from src.models.supplier_risk import calculate_supplier_risk
from src.models.commodity_risk import calculate_commodity_risk
from src.models.logistics_risk import calculate_logistics_risk
from src.models.geopolitical_risk import calculate_geopolitical_risk

WEIGHTS = {
    "supplier": 0.30,
    "commodity": 0.25,
    "logistics": 0.25,
    "geopolitical": 0.20,
}


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
    each of the 4 sub-scores, and the detailed breakdown behind each one (so the
    Week 3 dashboard can show both the headline number and what's driving it).
    """
    supplier_score = calculate_supplier_risk(industry)
    commodity_result = calculate_commodity_risk(industry)
    logistics_result = calculate_logistics_risk()
    geopolitical_result = calculate_geopolitical_risk(industry)

    sub_scores = {
        "supplier": supplier_score,
        "commodity": commodity_result["score"],
        "logistics": logistics_result["score"],
        "geopolitical": geopolitical_result["score"],
    }

    total = sum(sub_scores[key] * WEIGHTS[key] for key in WEIGHTS)

    return {
        "industry": industry,
        "total": round(total, 1),
        "label": get_risk_label(total),
        "sub_scores": {key: round(value, 1) for key, value in sub_scores.items()},
        "details": {
            "commodity": commodity_result,
            "logistics": logistics_result,
            "geopolitical": geopolitical_result,
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
              f"Logistics={s['logistics']} | Geopolitical={s['geopolitical']}")
