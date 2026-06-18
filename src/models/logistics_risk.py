from src.data.shipping import SHIPPING_STATUS, ROUTE_WEIGHTS
from src.data.news_alerts import get_route_alert

STATUS_BASE_SCORES = {
    "NORMAL": 0,
    "ELEVATED": 30,
    "DISRUPTED": 70,
    "SEVERE": 90,
}


def route_disruption_to_score(route_data):
    """Converts a route's hand-curated status into a 0-100 base score, by combining
    three factors via geometric mean (rather than a raw product, which would
    collapse toward 0 even when all three are merely "moderate"):
    - current_state: the status snapshot itself (NORMAL/ELEVATED/DISRUPTED/SEVERE)
    - probability: likelihood of continued disruption, proxied by typical delay days
    - impact: severity if disrupted, proxied by the cost premium

    Each factor is floored at 1 first - otherwise a NORMAL route (current_state=0)
    would always show exactly 0 even when it has a small real delay/cost premium,
    losing signal the previous additive model preserved.
    """
    current_state = STATUS_BASE_SCORES[route_data["status"]]
    probability = min(100, route_data["delay_days"] / 20 * 100)
    impact = min(100, route_data["cost_premium_pct"] / 40 * 100)
    combined = (max(current_state, 1) * max(probability, 1) * max(impact, 1)) ** (1 / 3)
    return min(100, combined)


def calculate_logistics_risk(use_news_alerts=True):
    """Returns the overall logistics risk score (same for all industries - major
    shipping routes affect global trade broadly) plus a per-route breakdown.

    Combines the slow hand-curated baseline (shipping.py, updated every 1-2 weeks)
    with the fast news-spike layer (news_alerts.py, refreshed daily) - so a sudden
    event that hasn't made it into the manual update yet still nudges the score.
    """
    total_score = 0
    by_route = {}

    for route, weight in ROUTE_WEIGHTS.items():
        base_score = route_disruption_to_score(SHIPPING_STATUS[route])

        alert_adjustment = 0
        if use_news_alerts:
            try:
                alert_adjustment = get_route_alert(route)["adjustment"]
            except Exception:
                alert_adjustment = 0  # NewsAPI hiccup shouldn't break the whole score

        final_score = min(100, base_score + alert_adjustment)
        by_route[route] = {
            "base": round(base_score, 1),
            "alert_adjustment": alert_adjustment,
            "final": round(final_score, 1),
        }
        total_score += final_score * weight

    return {"score": round(total_score, 1), "by_route": by_route}


if __name__ == "__main__":
    result = calculate_logistics_risk()
    print(f"=== Overall Logistics Risk = {result['score']} ===")
    for route, scores in result["by_route"].items():
        print(f"  {route}: base={scores['base']} alert=+{scores['alert_adjustment']} final={scores['final']}")
