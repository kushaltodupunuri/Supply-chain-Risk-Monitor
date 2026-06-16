# Hand-curated shipping route status. No free real-time API covers this well,
# so this is updated manually based on current shipping news. Update every 1-2 weeks.
# Last updated: 2026-06-16

SHIPPING_STATUS = {
    "Red Sea / Suez Canal": {
        "status": "DISRUPTED",
        "delay_days": 14,
        "cost_premium_pct": 40,
        "affected_trades": ["Asia-Europe", "Asia-Mediterranean"],
        "summary": "Houthi attacks causing rerouting around Cape of Good Hope since Dec 2023",
    },
    "Panama Canal": {
        "status": "ELEVATED",
        "delay_days": 3,
        "cost_premium_pct": 15,
        "affected_trades": ["Asia-East Coast US", "East Coast-West Coast"],
        "summary": "Drought reduced canal capacity; improved but not fully normal",
    },
    "US West Coast Ports": {
        "status": "NORMAL",
        "delay_days": 1,
        "cost_premium_pct": 5,
        "affected_trades": ["Trans-Pacific"],
        "summary": "Operating normally after 2023 labor agreement",
    },
    "US East Coast Ports": {
        "status": "NORMAL",
        "delay_days": 0,
        "cost_premium_pct": 0,
        "affected_trades": ["Trans-Atlantic", "South America"],
        "summary": "Operating normally",
    },
    "Strait of Malacca": {
        "status": "NORMAL",
        "delay_days": 0,
        "cost_premium_pct": 0,
        "affected_trades": ["Intra-Asia", "Middle East-Asia"],
        "summary": "Operating normally, no current disruptions reported",
    },
}

# How much of global container trade volume flows through each route.
# Used in Week 2 to weight the overall logistics risk score.
ROUTE_WEIGHTS = {
    "Red Sea / Suez Canal": 0.30,
    "Panama Canal": 0.15,
    "US West Coast Ports": 0.20,
    "US East Coast Ports": 0.15,
    "Strait of Malacca": 0.20,
}


def get_shipping_status():
    """Returns the current status of all tracked shipping routes."""
    return SHIPPING_STATUS


if __name__ == "__main__":
    print("=== Shipping Route Status ===")
    for route, data in get_shipping_status().items():
        print(f"\n{route} [{data['status']}]")
        print(f"  Delay: +{data['delay_days']} days | Cost premium: +{data['cost_premium_pct']}%")
        print(f"  Affected trades: {', '.join(data['affected_trades'])}")
        print(f"  Note: {data['summary']}")
