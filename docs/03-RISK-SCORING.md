# Risk Scoring — How Every Number Is Calculated

This explains the complete logic behind every score in the app. After reading this you will understand exactly what math is happening and why each decision was made.

---

## The Master Formula

Every industry gets one overall risk score from 0 to 100. It's a weighted average of four sub-scores:

```
Total Score = (Supplier × 0.30) + (Commodity × 0.25) + (Logistics × 0.25) + (Geopolitical × 0.20)
```

**Why these weights?**

- **Supplier Concentration (30%)** gets the highest weight because it determines your baseline fragility. If you source from 3 suppliers worldwide, no amount of price stability or calm geopolitics protects you from a single factory fire.
- **Commodity Price (25%)** and **Logistics (25%)** are equal because both directly affect cost and reliability in the near term. High commodity prices hurt margins. High logistics disruption hurts delivery.
- **Geopolitical (20%)** is important but slower-moving than prices and shipping. It's less reactive and more structural.

These weights are debatable — there's no single right answer. What matters is that you can explain your reasoning. These weights reflect a near-term operational risk lens (3-12 months), not a long-term strategic lens.

---

## Sub-Score 1: Supplier Concentration Risk (0-100)

**What it measures:** How dependent is this industry on a small number of suppliers or countries?

**The logic:**

Supplier concentration risk comes from two dimensions:
1. Geographic concentration — how many countries does this industry source from?
2. Single-source dependency — are there critical components with no substitute supplier?

Because getting exact supplier data for every industry in real time is hard, you use a combination of:
- Known structural facts (Electronics is 80%+ concentrated in Taiwan/South Korea for chips)
- Dynamic signals from UN Comtrade about trade flow concentration
- A base score per industry adjusted by current conditions

**Base concentration scores by industry (these change slowly, update quarterly):**

```python
BASE_SUPPLIER_SCORES = {
    "Electronics": 78,    # High: semiconductors are 80%+ in TW/KR, rare earths from China
    "Pharma": 72,         # High: ~70% of API ingredients come from China/India
    "Automotive": 61,     # Medium-High: chips from Asia, steel globally available
    "Retail": 55,         # Medium: diversified but still 40%+ from China
    "Food & Beverage": 35 # Lower: agricultural production is globally distributed
}
```

**Dynamic adjustment:** You adjust the base score based on current trade concentration data from UN Comtrade or news signals. If a country announces export restrictions on a key material, the score for affected industries goes up.

**Final calculation:**
```python
def calculate_supplier_risk(industry, adjustment=0):
    base = BASE_SUPPLIER_SCORES[industry]
    adjusted = min(100, max(0, base + adjustment))
    return adjusted
```

**Score interpretation:**
- 0-30: Well-diversified global sourcing base
- 31-60: Some concentration, manageable with dual sourcing
- 61-80: High concentration, one supplier failure causes problems
- 81-100: Critical single-source dependency, existential risk

---

## Sub-Score 2: Commodity Price Risk (0-100)

**What it measures:** Are the raw materials this industry needs getting more expensive and more volatile?

**The logic:**

This score combines two signals:
1. **Price trend** — Is the commodity more expensive than 90 days ago?
2. **Price volatility** — Is the price swinging unpredictably?

Both matter. A steadily rising price is bad (cost pressure). A volatile price is also bad (makes planning impossible, causes hedging costs).

**Step 1: Get the last 90 days of prices for each relevant commodity**

```python
def get_commodity_data_for_industry(industry):
    commodity_map = {
        "Electronics": ["COPPER", "WTI"],           # Copper (wiring), Oil (shipping)
        "Automotive": ["WTI", "ALUMINUM", "COPPER"],  # Oil, aluminum body, copper wiring
        "Pharma": ["NATURAL_GAS", "WTI"],            # Energy-intensive manufacturing
        "Retail": ["COTTON", "WTI"],                 # Cotton (clothing), Oil (shipping)
        "Food & Beverage": ["WHEAT", "CORN", "NATURAL_GAS"]  # Crops, energy
    }
    return commodity_map[industry]
```

**Step 2: Calculate trend score (0-100) for each commodity**

```python
def calculate_trend_score(prices):
    # prices is a list of daily values, most recent last
    recent_price = prices[-1]
    price_90_days_ago = prices[0]  # Assuming 90 days of data passed in
    
    pct_change = (recent_price - price_90_days_ago) / price_90_days_ago
    
    # Convert to 0-100 score
    # +30% change → score of 100 (very high risk)
    # -10% change → score of 0 (prices are falling, low risk)
    # 0% change → score of ~33
    
    score = max(0, min(100, (pct_change + 0.10) / 0.40 * 100))
    return score
```

**Step 3: Calculate volatility score (0-100)**

```python
import statistics

def calculate_volatility_score(prices):
    # Calculate coefficient of variation (standard deviation / mean)
    # This gives a normalized measure of volatility regardless of price level
    mean_price = statistics.mean(prices)
    std_price = statistics.stdev(prices)
    
    cv = std_price / mean_price  # Coefficient of variation
    
    # Scale: CV of 0.20 (20% swings) → score of 100 (very volatile)
    # CV of 0.02 (2% swings) → score of 0 (stable)
    score = min(100, (cv / 0.20) * 100)
    return score
```

**Step 4: Combine trend and volatility**

```python
def calculate_commodity_risk(industry):
    commodities = get_commodity_data_for_industry(industry)
    
    all_scores = []
    for commodity in commodities:
        prices = fetch_prices(commodity, days=90)  # From FRED or Alpha Vantage
        trend = calculate_trend_score(prices)
        volatility = calculate_volatility_score(prices)
        commodity_score = (trend * 0.6) + (volatility * 0.4)  # Trend matters more
        all_scores.append(commodity_score)
    
    return sum(all_scores) / len(all_scores)  # Average across commodities
```

**Why trend is weighted 60% and volatility 40%:** A rising price is immediately actionable (you lose margin). Volatility is a planning problem but not as acute. Adjust these if you want to emphasize planning risk more.

---

## Sub-Score 3: Logistics & Shipping Risk (0-100)

**What it measures:** Are major shipping routes disrupted? Are freight costs elevated?

**The logic:**

Each major shipping route has a status, a delay severity, and a cost premium. You score each route and then weight by how much global trade flows through it.

**Route weights (how much of global trade flows through each):**

```python
ROUTE_WEIGHTS = {
    "Red Sea / Suez Canal": 0.30,    # ~30% of global container volume
    "Panama Canal": 0.15,             # ~15% of global container volume
    "US West Coast Ports": 0.20,      # Major US import gateway
    "US East Coast Ports": 0.15,      # Major US import gateway
    "Strait of Malacca": 0.20         # Key Asia chokepoint
}
```

**Route disruption to score conversion:**

```python
def route_disruption_to_score(route_data):
    status = route_data["status"]
    delay_days = route_data["delay_days"]
    cost_premium_pct = route_data["cost_premium_pct"]
    
    # Base score from status
    status_scores = {
        "NORMAL": 0,
        "ELEVATED": 30,
        "DISRUPTED": 70,
        "SEVERE": 90
    }
    base = status_scores[status]
    
    # Adjust for delay severity
    delay_adjustment = min(20, delay_days * 1.5)
    
    # Adjust for cost premium
    cost_adjustment = min(10, cost_premium_pct * 0.3)
    
    return min(100, base + delay_adjustment + cost_adjustment)
```

**Final logistics score:**

```python
def calculate_logistics_risk():
    total_score = 0
    for route, weight in ROUTE_WEIGHTS.items():
        route_data = SHIPPING_STATUS[route]
        route_score = route_disruption_to_score(route_data)
        total_score += route_score * weight
    return total_score
```

**Note:** Logistics risk is the same for all industries because major shipping routes affect all trade. The only exception would be if a specific industry primarily uses air freight (some pharma) or rail (some domestic industries) — you can add industry adjustments later.

---

## Sub-Score 4: Geopolitical Risk (0-100)

**What it measures:** Are the countries this industry sources from politically stable? Are there active trade tensions that threaten supply?

**The logic:**

For each industry, you know which countries are the top 3-5 sourcing countries. You pull their political stability scores from the World Bank and weight by their share of sourcing.

**Sourcing country weights by industry:**

```python
INDUSTRY_SOURCING = {
    "Electronics": {
        "TW": 0.40,  # Taiwan - semiconductors
        "CN": 0.30,  # China - manufacturing
        "KR": 0.15,  # South Korea - memory chips
        "VN": 0.10,  # Vietnam - assembly
        "MY": 0.05   # Malaysia - packaging
    },
    "Pharma": {
        "CN": 0.40,  # China - API ingredients
        "IN": 0.30,  # India - generics
        "IE": 0.15,  # Ireland - branded drugs
        "SG": 0.15   # Singapore - biologics
    },
    "Automotive": {
        "CN": 0.30,  # China - batteries, electronics
        "MX": 0.25,  # Mexico - assembly
        "JP": 0.20,  # Japan - parts
        "DE": 0.15,  # Germany - premium components
        "KR": 0.10   # South Korea - parts
    },
    "Retail": {
        "CN": 0.45,  # China - manufacturing
        "BD": 0.20,  # Bangladesh - garments
        "VN": 0.20,  # Vietnam - manufacturing
        "IN": 0.15   # India - textiles
    },
    "Food & Beverage": {
        "US": 0.30,  # United States - domestic
        "BR": 0.25,  # Brazil - soybeans, meat
        "AR": 0.15,  # Argentina - grains
        "AU": 0.15,  # Australia - beef, wheat
        "UA": 0.15   # Ukraine - wheat, sunflower oil
    }
}
```

**World Bank political stability to risk conversion:**

The World Bank score goes from -2.5 (worst) to +2.5 (best). You convert to 0-100 risk:

```python
def wb_score_to_risk(wb_score):
    # wb_score: -2.5 to +2.5
    # -2.5 → risk 100 (most unstable)
    # +2.5 → risk 0 (most stable)
    risk = ((wb_score * -1) + 2.5) / 5.0 * 100
    return max(0, min(100, risk))
```

**Tariff/trade tension bonus:** You add a bonus to countries with active trade tensions:

```python
ACTIVE_TENSIONS = {
    "CN": 20,  # US-China tariffs, tech restrictions
    "TW": 15,  # Taiwan Strait geopolitical risk
    "RU": 30,  # Russia sanctions (not relevant to most industries but max for any Russian sourcing)
    "UA": 25   # Ukraine war ongoing
}

def calculate_geopolitical_risk(industry):
    sourcing = INDUSTRY_SOURCING[industry]
    total_score = 0
    
    for country, weight in sourcing.items():
        wb_score = get_country_risk(country, "GOV_WGI_PV.EST")
        base_risk = wb_score_to_risk(wb_score)
        tension_bonus = ACTIVE_TENSIONS.get(country, 0)
        country_risk = min(100, base_risk + tension_bonus)
        total_score += country_risk * weight
    
    return total_score
```

---

## Putting It All Together

```python
def calculate_risk_score(industry):
    supplier = calculate_supplier_risk(industry)
    commodity = calculate_commodity_risk(industry)
    logistics = calculate_logistics_risk()  # Same for all industries
    geopolitical = calculate_geopolitical_risk(industry)
    
    total = (
        supplier * 0.30 +
        commodity * 0.25 +
        logistics * 0.25 +
        geopolitical * 0.20
    )
    
    return {
        "total": round(total, 1),
        "supplier": round(supplier, 1),
        "commodity": round(commodity, 1),
        "logistics": round(logistics, 1),
        "geopolitical": round(geopolitical, 1)
    }
```

---

## Color Coding

The app uses this color scheme throughout:

```python
def get_risk_color(score):
    if score <= 30:
        return "#2ECC71"   # Green — Low Risk
    elif score <= 60:
        return "#F39C12"   # Yellow/Amber — Moderate Risk
    elif score <= 80:
        return "#E67E22"   # Orange — High Risk
    else:
        return "#E74C3C"   # Red — Critical Risk
```

---

## Expected Scores by Industry (Pre-Build Estimate vs. What Actually Got Computed)

The ranges below were a rough guess written before the model existed, just to sanity-check the build against. Once `risk_engine.py` was actually built and run (Week 2, June 2026), the real numbers came out noticeably lower across the board:

| Industry | Pre-Build Guess | Actually Computed | Why the Gap |
|----------|-----------------|--------------------|--------------|
| Electronics | 70-80 | 48.0 | Supplier risk (78) is genuinely high as predicted, but Commodity (28.7), Logistics (36.5), and Geopolitical (41.3) all came in moderate-low, and they're 70% of the weighted total. One high sub-score gets diluted fast. |
| Pharma | 65-75 | 46.9 | Same pattern: Supplier (72) high, everything else moderate. |
| Automotive | 60-70 | 44.2 | Same pattern. |
| Retail | 50-65 | 46.5 | Closest to the original guess. |
| Food & Beverage | 40-55 | 38.0 | Close to the original guess. |

**The real lesson here:** a 30%/25%/25%/20% weighted average naturally pulls extreme scores toward the middle unless *multiple* sub-scores are elevated at once. This isn't a bug - it's an honest property of the formula. If you want supplier concentration to dominate the headline number more (so Electronics' structural fragility isn't masked by calm commodity markets), that's a deliberate weighting decision to revisit, not something to "fix" by tweaking the data.

Also note: at the time these numbers were computed, the geopolitical news-alert layer (see [docs/02-DATA-SOURCES.md](02-DATA-SOURCES.md)) was returning 0 for every country because the NewsAPI free-tier daily quota had been exhausted during development testing. Geopolitical scores may run a few points higher once that layer is live again.

---

## Calibration Notes

**This scoring model is directionally correct, not precisely correct.** It will correctly identify Electronics as riskier than Food & Beverage. It will correctly show that commodity risk is rising when copper prices spike. That is the right goal.

It is NOT designed to give an absolute risk score that you'd stake financial decisions on. It's a dashboard tool for surfacing comparative risk and driving conversation, which is exactly what recruiters need to see you can build.

Real enterprise risk tools cost millions of dollars and have entire teams. You are showing you understand the concepts and can implement them. That's the point.

Next: [docs/04-BUILDING-THE-UI.md](04-BUILDING-THE-UI.md) — How to build the Streamlit dashboard.
