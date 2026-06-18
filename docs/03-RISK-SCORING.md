# Risk Scoring — How Every Number Is Calculated

This explains the complete logic behind every score in the app, matching the actual code in `src/models/`. After reading this you will understand exactly what math is happening and why each decision was made.

**This file has been rewritten twice as the model evolved.** The original build scored 4 categories across 5 industries. A later pass expanded to 7 categories (adding Currency/FX, Regulatory/Trade, and Climate/Disaster) across 11 industries. After hands-on review, **Currency/FX and Climate/Disaster were removed again** — the app now scores **5 risk dimensions** across **11 industries**, with an additional AI-driven company-specific adjustment layer. Every formula below matches what's actually in the code today.

---

## The Master Formula

Every industry gets one overall risk score from 0 to 100. It's a weighted average of **five** sub-scores (`src/models/risk_engine.py`). Weights can now vary **per industry** instead of one flat set across all 11:

```python
# Fallback, used by any industry without its own breakdown below
WEIGHTS = {
    "supplier": 0.25,
    "commodity": 0.20,
    "logistics": 0.20,
    "geopolitical": 0.20,
    "regulatory": 0.15,
}

WEIGHTS_BY_INDUSTRY = {
    "Electronics": {
        "supplier": 0.30, "geopolitical": 0.25, "commodity": 0.20,
        "logistics": 0.15, "regulatory": 0.10,
    },
    # Other 10 industries fall back to WEIGHTS above until they get their own
    # researched breakdown - Electronics' supplier-concentration weight was bumped
    # from 25% to 30% (and geopolitical from 20% to 25%) specifically because
    # semiconductor concentration matters more there than the industry-agnostic average.
}

def get_weights(industry):
    return WEIGHTS_BY_INDUSTRY.get(industry, WEIGHTS)
```

**Why these specific numbers?**

- **Supplier Concentration is the largest single factor (25%)** because it's a *multiplier* on every other risk, not an independent one. If you source a critical part from a single factory, calm commodity prices and stable politics don't protect you when that factory has a fire. It's also the slowest risk to fix — re-architecting a supplier base takes years — so getting it wrong has the longest-lasting consequences.

- **Commodity, Logistics, and Geopolitical are tied at 20% each** because each can independently and immediately disrupt a supply chain through a different mechanism: Commodity hits margins directly, Logistics hits delivery reliability directly, and Geopolitical is the "umbrella" risk that can suddenly trigger the other two at once (a new tariff or war can spike commodity costs and disrupt shipping simultaneously). None is consistently more severe than the others across all 11 industries, so they're weighted equally rather than asserting a false hierarchy.

- **Regulatory gets the smallest weight (15%)** not because it matters less, but because it overlaps with the other categories more than it stands alone — a new tariff usually shows up as a Commodity cost increase or a Geopolitical event too. Weighting it the same as the other three would effectively double-count part of that risk.

These weights are a judgment call, not a law of physics — what matters is that you can explain your reasoning, and that one extreme sub-score doesn't accidentally dominate or get buried (see "Calibration Notes" below for what actually happens in practice).

---

## Sub-Score 1: Supplier Concentration Risk (0-100)

**File:** `src/models/supplier_risk.py`

**What it measures:** How dependent is this industry on a small number of suppliers or countries?

**The logic:** This is intentionally a **hand-curated, static baseline**, not pulled from a live API. Supplier concentration is structural — it shifts over years, not days — so there's no value (and real risk of fabrication) in pretending to compute it from a live feed. The values are researched judgment calls, revisited periodically:

```python
BASE_SUPPLIER_SCORES = {
    "Electronics": 78,                       # 80%+ of advanced semiconductors made in Taiwan/South Korea
    "Pharma": 72,                            # ~70% of active pharmaceutical ingredients from China/India
    "IT": 75,                                # Same semiconductor dependency as Electronics, plus cloud/hyperscaler concentration
    "Aerospace & Defense": 70,               # Highly specialized, concentrated supplier base
    "Automotive": 61,                        # Chips concentrated in Asia, steel/aluminum globally available
    "Retail": 55,                            # Diversifying, but still 40%+ manufacturing from China
    "Energy": 50,                            # OPEC+ concentration in extraction, refining is diversified
    "Industrial Equipment & Machinery": 50,  # Moderate - components sourced broadly
    "Chemicals": 45,                         # Moderate - feedstock concentration offset by global production
    "E-commerce": 45,                        # Logistics-driven, not manufacturing-concentrated
    "Food & Beverage": 35,                   # Agricultural production is globally distributed
}

def calculate_supplier_risk(industry, adjustment=0):
    base = BASE_SUPPLIER_SCORES[industry]
    return max(0, min(100, base + adjustment))
```

`adjustment` exists so you can manually nudge a score (e.g. +10 if a major supplier announces an outage) without needing a live feed for something this slow-moving.

**Score interpretation:**
- 0-30: Well-diversified global sourcing base
- 31-60: Some concentration, manageable with dual sourcing
- 61-80: High concentration, one supplier failure causes problems
- 81-100: Critical single-source dependency, existential risk

---

## Sub-Score 2: Commodity Price Risk (0-100)

**File:** `src/models/commodity_risk.py`

**What it measures:** Are the raw materials this industry needs getting more expensive and more volatile?

**The commodities tracked (8 total, `src/data/commodity_prices.py`):** Steel, Copper, Aluminum, Oil (WTI), Natural Gas, Wheat, Corn, Cotton, and Titanium — sourced from FRED (Steel, Titanium) and Alpha Vantage (everything else).

```python
INDUSTRY_COMMODITIES = {
    "Automotive": ["Steel", "Copper", "Aluminum", "Oil (WTI)"],
    "Electronics": ["Copper", "Oil (WTI)"],
    "Pharma": ["Natural Gas", "Oil (WTI)"],
    "Retail": ["Cotton", "Oil (WTI)"],
    "Food & Beverage": ["Wheat", "Corn", "Natural Gas"],
    "Energy": ["Oil (WTI)", "Natural Gas"],
    "Aerospace & Defense": ["Aluminum", "Titanium", "Oil (WTI)"],
    "Chemicals": ["Oil (WTI)", "Natural Gas"],
    "Industrial Equipment & Machinery": ["Steel", "Copper", "Aluminum"],
    "IT": ["Copper", "Oil (WTI)"],
    "E-commerce": ["Oil (WTI)", "Cotton"],
}
```

**Important real-world data quirk:** Oil and Natural Gas come back as true **daily** prices. Copper, Aluminum, Wheat, Corn, Cotton, Steel, and Titanium only have **monthly** data on the free API tier. Early on, naively comparing "the last 90 entries" would have compared 90 *months* (7.5 years) for the monthly commodities instead of 90 days. The fix: `_filter_to_window()` filters price history by actual calendar date before any math runs, regardless of how many raw entries came back.

**Step 1: Filter to the actual calendar window, then calculate trend**

```python
def calculate_trend_score(prices, days=90):
    windowed = _filter_to_window(prices, days)
    if len(windowed) < 2:
        windowed = prices[-2:] if len(prices) >= 2 else prices  # fallback for sparse monthly data
    if len(windowed) < 2:
        return 50  # can't compute a trend from one point - treat as unknown/moderate

    old_price, recent_price = windowed[0]["value"], windowed[-1]["value"]
    pct_change = (recent_price - old_price) / old_price
    score = (pct_change + 0.10) / 0.40 * 100  # +30% change -> 100, -10% change -> 0
    return max(0, min(100, score))
```

**Step 2: Calculate volatility (coefficient of variation)**

```python
def calculate_volatility_score(prices, days=90):
    windowed = _filter_to_window(prices, days)
    if len(windowed) < 3:
        windowed = prices[-6:] if len(prices) >= 6 else prices
    values = [item["value"] for item in windowed]
    if len(values) < 3:
        return 30  # too few points to measure volatility meaningfully

    cv = statistics.stdev(values) / statistics.mean(values)
    score = (cv / 0.20) * 100  # CV of 20% swings -> 100 (very volatile)
    return max(0, min(100, score))
```

**Step 3: Calculate "Current State" — where today's price sits in its own recent range**

```python
def calculate_current_state_score(prices, days=90):
    windowed = _filter_to_window(prices, days)
    values = [item["value"] for item in windowed]
    latest, lo, hi = values[-1], min(values), max(values)
    if hi == lo:
        return 50
    return max(0, min(100, (latest - lo) / (hi - lo) * 100))  # 100 = at/near the period high
```

This is what makes Current State distinct from trend: a commodity that spiked mid-window and has since retreated has a high trend score but a low Current State score — it already moved, but today isn't the exposed moment.

**Step 4: Combine as Probability x Impact x Current State, via geometric mean**

```python
probability = calculate_volatility_score(history)      # how likely it keeps swinging
impact = calculate_trend_score(history)                  # how much it's already moved
current_state = calculate_current_state_score(history)   # where today sits in that range

combined = (max(probability, 1) * max(impact, 1) * max(current_state, 1)) ** (1 / 3)
overall_score = average(combined across all commodities for the industry)
```

**Why geometric mean, not a raw product?** A raw product of three 0-100 scores treated as fractions collapses toward 0 even when all three are merely "moderate" — 0.5 x 0.5 x 0.5 = 0.125, which would make every commodity look artificially low-risk. Geometric mean keeps three "50" inputs combining to ~50 (matching intuition) while still pulling the score down hard if any one dimension is genuinely low — the same "all three must align for high risk" property a raw product has, without the scale collapse. Each factor is floored at 1 before combining, since a single factor hitting exactly 0 (e.g. today happens to be the exact period low) would otherwise force the whole geometric mean to 0, hiding real risk on the other two dimensions.

**This replaced the original `trend * 0.6 + volatility * 0.4` weighted-sum formula** described in earlier versions of this doc — that version only used two signals and combined them additively, which doesn't reward (or penalize) all three dimensions aligning the way a true risk-multiplier model should.

---

## Sub-Score 3: Logistics & Shipping Risk (0-100)

**File:** `src/models/logistics_risk.py`

**What it measures:** Are major shipping routes disrupted? Are freight costs elevated? This score is **the same for every industry** — major shipping routes affect global trade broadly, regardless of what's being shipped.

**Two-layer design:** a slow, hand-curated baseline (`src/data/shipping.py`, updated every 1-2 weeks) combined with a fast, live news-spike layer (`src/data/news_alerts.py`, refreshed daily) that catches sudden disruptions between manual updates.

```python
ROUTE_WEIGHTS = {
    "Red Sea / Suez Canal": 0.30,
    "Panama Canal": 0.15,
    "US West Coast Ports": 0.20,
    "US East Coast Ports": 0.15,
    "Strait of Malacca": 0.20,
}

STATUS_BASE_SCORES = {"NORMAL": 0, "ELEVATED": 30, "DISRUPTED": 70, "SEVERE": 90}

def route_disruption_to_score(route_data):
    """Probability x Impact x Current State, via geometric mean - same pattern as
    Commodity. current_state is the status snapshot itself; probability is proxied
    by typical delay days (a longer typical delay implies more probable ongoing
    disruption); impact is proxied by the cost premium.
    """
    current_state = STATUS_BASE_SCORES[route_data["status"]]
    probability = min(100, route_data["delay_days"] / 20 * 100)
    impact = min(100, route_data["cost_premium_pct"] / 40 * 100)
    combined = (max(current_state, 1) * max(probability, 1) * max(impact, 1)) ** (1 / 3)
    return min(100, combined)

def calculate_logistics_risk(use_news_alerts=True):
    total_score = 0
    for route, weight in ROUTE_WEIGHTS.items():
        base_score = route_disruption_to_score(SHIPPING_STATUS[route])
        alert_adjustment = get_route_alert(route)["adjustment"] if use_news_alerts else 0
        final_score = min(100, base_score + alert_adjustment)
        total_score += final_score * weight
    return total_score
```

**This replaced the original additive formula** (`base + min(20, delay*1.5) + min(10, cost*0.3)`) for the same reason as Commodity above — a true Probability x Impact x Current State model should require all three dimensions to align for a high score, not just sum up independent bonuses. Each factor is floored at 1 before combining; without that floor, a NORMAL route (current_state=0) would always show exactly 0 even when it has a small real delay/cost premium (e.g. "US West Coast Ports" is NORMAL but still carries +1 day / +5% cost), losing signal the original additive model preserved.

See "The Fast Alert Layer" section below for exactly how `alert_adjustment` is computed and why it took several iterations to get right.

---

## Sub-Score 4: Geopolitical Risk (0-100)

**File:** `src/models/geopolitical_risk.py`

**What it measures:** Are the countries this industry sources from politically stable? Are there active trade tensions or breaking events?

**This replaced the original hand-coded `ACTIVE_TENSIONS` bonus dict** from the first version of this doc. Instead of a static "China gets +20, Taiwan gets +15" table, the geopolitical score now combines a real World Bank baseline with the **same live news-alert layer** used for logistics:

```python
def wb_score_to_risk(wb_score):
    # World Bank's Political Stability score: -2.5 (worst) to +2.5 (best)
    risk = ((wb_score * -1) + 2.5) / 5.0 * 100
    return max(0, min(100, risk))

def calculate_geopolitical_risk(industry, use_news_alerts=True):
    sourcing = INDUSTRY_SOURCING_WEIGHTS[industry]
    total_score = 0
    for code, weight in sourcing.items():
        wb_data = get_country_risk(code)  # World Bank API, cached 7 days
        base_risk = wb_score_to_risk(wb_data["value"])
        alert_adjustment = get_country_alert(COUNTRY_NAMES[code])["adjustment"] if use_news_alerts else 0
        final_risk = min(100, base_risk + alert_adjustment)
        total_score += final_risk * weight
    return total_score
```

**Real bug fixed here:** the World Bank's short indicator codes (e.g. `PV.EST`) point to an *archived* data source and silently fail. The live, current code is `GOV_WGI_PV.EST` (source ID 3, "Worldwide Governance Indicators") — found by querying World Bank's source catalog directly after the short code returned "indicator not found."

Each of the 11 industries has its own researched sourcing-country weights and **what's actually sourced from each country** (shown in the app's Geopolitical Map tab), e.g.:

```python
INDUSTRY_SOURCING_WEIGHTS = {
    "Electronics": {"TW": 0.40, "CN": 0.30, "KR": 0.15, "VN": 0.10, "MY": 0.05},
    "Energy": {"US": 0.35, "SA": 0.25, "RU": 0.15, "CA": 0.25},
    "Aerospace & Defense": {"US": 0.40, "FR": 0.20, "JP": 0.15, "DE": 0.15, "GB": 0.10},
    # ...11 industries total, see geopolitical_risk.py for the full set
}

INDUSTRY_SOURCING_PRODUCTS = {
    "Electronics": {
        "TW": "Advanced semiconductors & chips (TSMC foundries)",
        "CN": "Final assembly, PCBs & general components (Foxconn and others)",
        # ...
    },
}
```

---

## Sub-Score 5: Regulatory & Trade Risk (0-100)

**File:** `src/models/regulatory_risk.py`

**What it measures:** Tariffs, export controls, trade agreements, customs disputes — anything that could disrupt the legal/political terms of trade for this industry.

**Two-layer design, same pattern as Logistics:** a hand-curated baseline reflecting currently known trade exposure, plus a live news-spike layer watching for sudden tariff/trade-policy headlines.

```python
REGULATORY_BASELINE = {
    "Electronics": {"base_score": 55, "summary": "Ongoing US-China semiconductor export controls and tariffs"},
    "Aerospace & Defense": {"base_score": 60, "summary": "Export controls (ITAR) and defense procurement regulations"},
    "Pharma": {"base_score": 30, "summary": "Relatively stable trade environment currently"},
    # ...11 industries total
}

def calculate_regulatory_risk(industry, use_news_alerts=True):
    baseline = REGULATORY_BASELINE[industry]
    alert_adjustment = get_industry_alert(industry, REGULATORY_KEYWORDS, "regulatory")["adjustment"] if use_news_alerts else 0
    return min(100, baseline["base_score"] + alert_adjustment)
```

`REGULATORY_KEYWORDS` = tariff, trade war, export control, import ban, trade agreement, customs, trade restriction, trade deal, WTO dispute.

---

## Why Currency/FX and Climate/Disaster Were Removed

Both were built, tested, and working correctly (Currency used real FRED exchange-rate volatility; Climate used a hand-curated baseline plus a live disaster-news layer, same pattern as Regulatory). They were removed from the active model after review - not because the underlying logic was wrong, but because they were judged to add more noise than signal for what this dashboard needs to communicate. The code paths (`currency_risk.py`, `climate_risk.py`, `data/currency.py`, `CLIMATE_KEYWORDS`) were deleted outright rather than left disabled-but-present, since dead code that nothing imports is just confusion waiting to happen later.

If you want to bring either back, the Currency design (FX volatility via FRED, direction-agnostic on purpose) and Climate design (hand-curated baseline + news-spike layer) are both still described in this project's git history and were genuinely sound implementations - this is a "removed by product judgment," not "removed because broken," distinction worth preserving.

---

## The Fast Alert Layer (shared by Logistics, Geopolitical, Regulatory)

**File:** `src/data/news_alerts.py`

Three of the five sub-scores layer a live NewsAPI-driven signal on top of a slow baseline. This module went through several real, found-by-testing bug fixes worth understanding if you extend it:

1. **Ratio, not raw count.** A naturally newsworthy country (China) always has thousands of risk-keyword mentions; a quiet one (Vietnam) might have a handful. Comparing each subject's *current week* to its *own* trailing-30-day baseline — not an absolute count — is what lets a genuine spike stand out for either, instead of permanently pegging noisy subjects at max risk.

2. **Headline-only search (`qInTitle`), not full-text.** Full-text search caused major false positives — e.g. during the 2026 World Cup, articles about Mexico/Brazil/Argentina incidentally contained risk-sounding words ("crackdown," "conflict") deep in unrelated body text about sports, not supply chains.

3. **Multi-word keywords must be quoted individually.** `"export ban"` left unquoted in a keyword list gets parsed by NewsAPI as the separate words "export" OR "ban" — which once caused bare "ban" to match cricket score recaps ("BAN vs AUS," BAN being the abbreviation for Bangladesh's cricket team) and an unrelated social-media-ban news story.

4. **`MIN_RECENT_COUNT_FOR_ALERT` guardrail.** A quiet subject with a tiny baseline (1.2 articles/week) can swing to "4 articles this week" and look like a 300% spike — pure sample noise, not a real signal. A minimum absolute volume must be hit before any adjustment fires, regardless of how dramatic the ratio looks.

```python
def ratio_to_adjustment(ratio):
    if ratio >= 2.5: return 20
    elif ratio >= 1.8: return 12
    elif ratio >= 1.3: return 6
    elif ratio >= 1.1: return 2
    return 0

MIN_RECENT_COUNT_FOR_ALERT = 3
```

---

## The Company-Specific Adjustment Layer

**File:** `src/ai/summary.py`

When a company name is entered, four AI-driven (Groq/Ollama) functions can adjust what's displayed — all using the same core honesty rule: **if the model isn't genuinely confident it has real, specific knowledge of the company, it must say so and change nothing**, rather than fabricating plausible-looking specifics.

1. **`detect_company_industry()`** — identifies which of the 11 industries the company belongs to, and the sidebar's industry dropdown auto-syncs to match (so typing "Apple" works correctly even if "Automotive" happens to be selected).
2. **`generate_company_score_adjustment()`** — estimates a -15 to +15 nudge per sub-score (across all 5 current dimensions) based on real, named facts (e.g. Apple's Foxconn relationship), defaulting to 0 across the board if the company isn't recognized with high confidence.
3. **`generate_company_sourcing_countries()`** — for recognized companies, lists their *actual* known sourcing countries (often more than the generic industry's 4-5), used to replace the generic Geopolitical Map breakdown with something company-specific.
4. **`generate_known_suppliers()`** — names specific, real suppliers (e.g. TSMC, Foxconn) when genuinely known, feeding the High-Risk Suppliers list and the Supplier Compliance Status check (see "New Dashboard Sections" below).

**This calibration took two real iterations.** The first prompt version confidently fabricated detailed, plausible-sounding sourcing breakdowns for entirely made-up company names ("Globex Manufacturing Solutions," "ZX Quark Dynamics Inc"). The fix was an explicit instruction to treat generic-sounding or unfamiliar names as NOT known by default, and to require the model name a *specific, real fact* before marking anything as known — verified by testing against both real companies and deliberately fictional/plausible-sounding fake ones.

**A second real bug, found later:** none of these calls had a fixed temperature or random seed, so the same company could get a *different* score adjustment on a different device, after a cache expiry, or on a different LLM provider — a real non-determinism bug, not just normal AI variation, since this is a number meant to be a stable fact about a company, not creative writing. Fixed by pinning `temperature=0` and `seed=42` on all four functions above. The prose-only functions (`generate_risk_summary`, `generate_recommendations`' detail text) keep the default temperature, since natural variation in wording doesn't undermine trust in the number the way a wrong number would.

---

## New Dashboard Sections (Beyond the 5 Core Sub-Scores)

Three sections present the same underlying real data from a different angle, rather than computing anything new from scratch:

**Supplier Risk** (`Risk_Monitor.py`, reuses `supplier_risk.py` + `sanctions.py`):
- *Supplier Risk Rating* — the Supplier Concentration score, restated.
- *Single Source Dependency* — High/Moderate/Low based on the top sourcing country's share of total sourcing (≥50% / ≥30% / below).
- *Supplier Compliance Status* — a real check of named suppliers (or the typed company name, if no suppliers are known) against the US Treasury's Consolidated Screening List via trade.gov's API. Shows "Not checked" honestly if no API key is configured, rather than a false "Clear."

**Logistics Risk** (`Risk_Monitor.py`, reuses `logistics_risk.py` + `shipping.py`):
- *Shipment Delays* — the weighted average `delay_days` across tracked routes.
- *Port Congestion* — the average risk score across routes whose name contains "Port".
- *Transportation Risk Index* — the Logistics & Shipping score, restated.
- *On-Time Delivery Rate* — `100 - logistics_score * 0.4`, floored at 60%, explicitly labeled as an **estimate derived from** the Transportation Risk Index, since no free API publishes real carrier on-time performance data.

**Geographic & External Risk** (`Risk_Monitor.py`, reuses `news_alerts.py` + the 5 core scores):
- *Natural Disaster Alerts*, *Weather Impact*, *Regional Conflict Alerts* — three new live NewsAPI keyword-spike checks (see "API #4: NewsAPI" in [docs/02-DATA-SOURCES.md](02-DATA-SOURCES.md) for the keyword sets) against the top sourcing country, banded Normal/Watch/Elevated/High by the same `ratio_to_adjustment()` thresholds used everywhere else.
- *Political/Regulatory Risks* — the average of the Geopolitical and Regulatory & Trade scores.

**Dashboard Visualization** (`src/charts.py`, `src/data/score_history.py`):
- *Risk Ranking* — a horizontal stacked bar chart, all 11 industries sorted by overall score, each bar segmented by `score * weight` per category so the bar length sums exactly to that industry's real overall score. Replaced an earlier color-intensity heat map after feedback that color grids are hard to compare precisely by eye.
- *Trend Analysis* — the current industry's overall score, snapshotted once per calendar day to a local JSON file (`record_score_snapshot`) and plotted over time. Starts with a single point and genuinely accumulates — there's no way to back-fill real history for a scoring formula that didn't exist before today.

An "Executive Summary" section (Critical Risk Alerts, High-Risk Suppliers, Disruption Probability) was added, then **removed** after review — see [PLAN.md](../PLAN.md) for the full reasoning. The Overall Risk Score itself stayed visible everywhere it already was (the gauge chart, the PDF's colored score box, Excel's Overview sheet); only the three sub-lists were cut.

---

## Putting It All Together

```python
def calculate_risk_score(industry):
    sub_scores = {
        "supplier": calculate_supplier_risk(industry),
        "commodity": calculate_commodity_risk(industry)["score"],
        "logistics": calculate_logistics_risk()["score"],
        "geopolitical": calculate_geopolitical_risk(industry)["score"],
        "regulatory": calculate_regulatory_risk(industry)["score"],
    }
    weights = get_weights(industry)  # per-industry if defined, else the flat fallback
    total = sum(sub_scores[key] * weights[key] for key in weights)
    return {
        "total": round(total, 1),
        "label": get_risk_label(total),
        "sub_scores": sub_scores,
        "weights": weights,
        "details": {...},  # the raw per-commodity/route/country breakdowns, used by drill-downs and exports
    }
```

---

## Color Coding

```python
def get_risk_color(score):
    if score <= 30: return "#2ECC71"   # Green - Low Risk
    elif score <= 60: return "#F39C12" # Amber - Moderate Risk
    elif score <= 80: return "#E67E22" # Orange - High Risk
    else: return "#E74C3C"             # Red - Critical Risk
```

The same thresholds back `get_risk_label()`, which is what shows the "Low/Moderate/High/Critical Risk" text under each score card in the app.

---

## The 11 Industries

| Industry | Added | Notable Commodities |
|---|---|---|
| Electronics, Automotive, Pharma, Retail, Food & Beverage | Original build | Copper, Steel, Cotton, Wheat, etc. |
| Energy, Aerospace & Defense, Chemicals, Industrial Equipment & Machinery, IT, E-commerce | Added later | Oil/Natural Gas, **Titanium** (new), Steel/Copper, Copper, Cotton |

Adding Aerospace & Defense required adding a real Titanium price series (FRED `WPU102505`, monthly PPI data — same pattern as Steel) since Alpha Vantage's free commodity API doesn't cover it.

---

## Expected Scores by Industry (Pre-Build Estimate vs. What Actually Got Computed)

This table is preserved from the original 4-category build as an honest record of a real lesson, not because the numbers below still reflect the current 7-category model (they don't — adding 3 more categories changed every total):

| Industry | Pre-Build Guess (4-category) | Actually Computed (4-category) | Why the Gap |
|----------|-----------------|--------------------|--------------|
| Electronics | 70-80 | 48.0 | Supplier risk (78) is genuinely high as predicted, but Commodity, Logistics, and Geopolitical all came in moderate-low, and they're 70% of the weighted total. One high sub-score gets diluted fast. |
| Pharma | 65-75 | 46.9 | Same pattern. |
| Automotive | 60-70 | 44.2 | Same pattern. |
| Retail | 50-65 | 46.5 | Closest to the original guess. |
| Food & Beverage | 40-55 | 38.0 | Close to the original guess. |

**The real lesson:** a weighted average naturally pulls extreme scores toward the middle unless *multiple* sub-scores are elevated at once. This isn't a bug — it's an honest property of the formula. If you want one dimension (e.g. supplier concentration) to dominate the headline number more, that's a deliberate weighting decision to revisit, not something to "fix" by tweaking the data.

---

## Calibration Notes

**This scoring model is directionally correct, not precisely correct.** It will correctly identify Electronics as riskier than Food & Beverage on supplier concentration. It will correctly show commodity risk rising when copper prices spike. It will correctly flag a real news-driven spike (validated during testing) while ignoring naturally noisy countries' background chatter. That is the right goal.

It is NOT designed to give an absolute risk score you'd stake financial decisions on. It's a dashboard tool for surfacing comparative risk and driving conversation — and for a portfolio project, demonstrating that you understand *why* each number exists, not just that a number exists.

Real enterprise risk tools cost millions of dollars and have entire teams. You are showing you understand the concepts, can implement them with real data, and can find and fix your own bugs when the data doesn't behave as expected. That's the point.
