# Supplier concentration is structural - sourcing patterns shift over years, not days.
# These base scores reflect researched industry sourcing concentration and should be
# revisited quarterly, not pulled from a live API. Higher = more dependent on a small
# number of suppliers/countries.
BASE_SUPPLIER_SCORES = {
    "Electronics": 78,     # 80%+ of advanced semiconductors made in Taiwan/South Korea
    "Pharma": 72,           # ~70% of active pharmaceutical ingredients from China/India
    "Automotive": 61,       # Chips concentrated in Asia, but steel/aluminum globally available
    "Retail": 55,           # Diversifying, but still 40%+ manufacturing from China
    "Food & Beverage": 35,  # Agricultural production is globally distributed
}


def calculate_supplier_risk(industry, adjustment=0):
    """Returns a 0-100 supplier concentration score.

    `adjustment` lets you manually nudge the score (e.g. +10 if a major supplier
    announces an outage) without needing a live data feed for something this slow-moving.
    """
    if industry not in BASE_SUPPLIER_SCORES:
        raise ValueError(f"Unknown industry: {industry}")

    base = BASE_SUPPLIER_SCORES[industry]
    return max(0, min(100, base + adjustment))


if __name__ == "__main__":
    for industry in BASE_SUPPLIER_SCORES:
        score = calculate_supplier_risk(industry)
        print(f"{industry}: {score}/100")
