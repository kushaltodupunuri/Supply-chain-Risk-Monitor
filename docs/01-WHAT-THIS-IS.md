# What This App Is — Plain English Explanation

Read this first. It explains what you're building, why each part exists, and how the pieces connect. No jargon.

**This doc was rewritten to match the live app.** The original plan covered 5 industries and 4 risk categories. The app has since grown to **11 industries** and **5 risk categories** (Currency/FX and Climate/Disaster were tried, then removed after review — see [docs/03-RISK-SCORING.md](03-RISK-SCORING.md) for why), plus a company-specific AI layer, a PDF/Excel export, and three additional dashboard sections (Supplier Risk, Logistics Risk, Geographic & External Risk) that weren't in the original plan at all.

---

## The One-Line Description

You are building a website that looks at live real-world data — commodity prices, shipping news, geopolitical events, trade policy — and turns it into a single risk score for a given industry's (or company's) supply chain.

---

## What Problem Does It Solve?

Supply chain managers at companies like Apple, GM, or Pfizer spend hours every week trying to answer one question:

**"How exposed are we right now, and what's the biggest threat?"**

They have to check commodity prices (steel went up 15% last month), look at shipping news (Red Sea disruptions adding 3 weeks to Asia-Europe routes), read geopolitical reports (new US-China tariffs coming), and then somehow combine all of this into a clear picture.

Your app does that automatically, in seconds, for any industry — or for a specific company, if the AI recognizes it.

---

## The 11 Industries You Cover

You started with 5 and later added 6 more, covering a much wider range of recruiter-relevant sectors:

| Industry | Main Risks | Key Commodities |
|----------|-----------|-----------------|
| **Electronics** | Taiwan semiconductor concentration, rare earths | Copper, oil |
| **IT** | Same chip dependency as Electronics, plus cloud/hyperscaler concentration | Copper, oil |
| **Aerospace & Defense** | Concentrated, specialized supplier base, export controls (ITAR) | Aluminum, titanium, oil |
| **Pharma** | API sourcing from China/India | Natural gas, oil |
| **Automotive** | Semiconductor shortage, raw material prices | Steel, copper, aluminum, oil |
| **Energy** | OPEC+ concentration, sanctions on Russian exports | Oil, natural gas |
| **Retail** | Ocean freight volatility, Asian manufacturing | Cotton, oil |
| **E-commerce** | Logistics-driven, less manufacturing-concentrated | Oil, cotton |
| **Industrial Equipment & Machinery** | Components sourced broadly, assembly more concentrated | Steel, copper, aluminum |
| **Chemicals** | Feedstock concentration offset by global production | Oil, natural gas |
| **Food & Beverage** | Weather, agricultural commodities, fuel | Wheat, corn, natural gas |

Each industry has its own researched supplier-concentration score, sourcing-country breakdown, and regulatory exposure — not one generic model stretched across all 11. Aerospace & Defense needed a brand-new commodity (Titanium) added to the data layer, since none of the original 8 commodities applied to it.

---

## The Five Risk Dimensions

Every supply chain is scored across the same five categories, each 0-100, combined into one weighted total.

### 1. Supplier Concentration Risk (25% of total score)

**What it means:** Are you buying from too few suppliers in too few countries?

If Apple buys most of its semiconductors from TSMC in Taiwan, and something happens in Taiwan, Apple has no backup. That's high concentration risk.

**How you measure it:** A hand-researched baseline score per industry (Electronics and IT score highest due to Taiwan/South Korea chip concentration; Food & Beverage scores lowest since agriculture is globally distributed). This is intentionally *not* pulled from a live API — supplier concentration shifts over years, not days, so a static, researched number is more honest than pretending to compute it live.

**This is 25% of the total** — the single largest factor — because sourcing concentration is the most fundamental supply chain risk.

### 2. Commodity Price Risk (20% of total score)

**What it means:** Are the raw materials this industry needs spiking in price or becoming volatile?

**How you measure it:** Live commodity price data (FRED + Alpha Vantage) across 9 tracked commodities (Steel, Copper, Aluminum, Titanium, Oil, Natural Gas, Wheat, Corn, Cotton). Three real signals combine as **Probability × Impact × Current State**: historical volatility (how likely is it to keep swinging), trend magnitude (how much has it already moved), and where today's price sits within its own recent range (a price that spiked and retreated reads differently than one still climbing). See [docs/03-RISK-SCORING.md](03-RISK-SCORING.md) for why this is combined as a geometric mean, not a raw product.

### 3. Logistics & Shipping Risk (20% of total score)

**What it means:** Can goods actually move from where they're made to where they're needed?

**How you measure it:** Same Probability × Impact × Current State approach as Commodity, built from the existing hand-curated route data: the status snapshot itself (NORMAL/ELEVATED/DISRUPTED/SEVERE) as Current State, typical delay days as Probability, and the cost premium as Impact — combined via geometric mean, then a **live news-spike layer** adds on top to catch breaking disruption headlines between manual route-status updates.

### 4. Geopolitical Risk (20% of total score)

**What it means:** Are there political tensions, trade wars, or sanctions that could cut off supply?

**How you measure it:** Real World Bank political-stability data per sourcing country, weighted by how much of that industry's supply chain runs through each country, combined with the same live news-spike layer used for Logistics.

### 5. Regulatory & Trade Risk (15% of total score)

**What it means:** Tariffs, export controls, trade agreements, customs disputes — anything that disrupts the *legal* terms of trade, separate from political stability itself.

**How you measure it:** A hand-curated baseline per industry (e.g. Electronics and IT score high due to ongoing semiconductor export controls) plus the same live news-spike layer, watching for tariff/trade-policy headlines specifically.

---

## How the Score Is Calculated

```
Total Risk Score = (Supplier × weight) + (Commodity × weight) + (Logistics × weight) + (Geopolitical × weight) + (Regulatory × weight)
```

The weights themselves can now vary **per industry** (`WEIGHTS_BY_INDUSTRY` in `risk_engine.py`), since the same dimension doesn't matter equally everywhere — semiconductor-dependent Electronics has a custom breakdown (Supplier 30% / Geopolitical 25% / Commodity 20% / Logistics 15% / Regulatory 10%). The other 10 industries currently fall back to the original flat split below until they get their own researched breakdown:

```
Supplier 25% / Commodity 20% / Logistics 20% / Geopolitical 20% / Regulatory 15%
```

**Why these specific numbers, not some other split?**

- **Supplier Concentration gets the largest weight (25%)** because it's a *multiplier* on every other risk, not just another independent risk. If you source a critical part from one factory, calm commodity prices and stable politics don't save you when that factory has a fire. It's also the slowest risk to fix — re-architecting a supplier base takes years, not weeks — so getting this one wrong has the longest-lasting consequences.

- **Commodity, Logistics, and Geopolitical are tied at 20% each** because they're the three risks that can each independently and immediately disrupt a supply chain, just through different mechanisms: Commodity hits your margins directly (a price spike shows up on the P&L next quarter), Logistics hits your delivery reliability directly (the goods exist but can't move), and Geopolitical is the "umbrella" risk that can suddenly *trigger* the other two at once (a new tariff or war can spike commodity costs and disrupt shipping routes simultaneously). None of the three is consistently more severe than the others across all 11 industries, so they're weighted equally rather than guessing a false hierarchy.

- **Regulatory gets the smallest weight (15%)**, not because it doesn't matter, but because it overlaps with the other categories more than it stands alone — a new tariff usually shows up as a Commodity cost increase or a Geopolitical event too. Weighting it the same as the other three would effectively double-count a chunk of that risk.

These weights are a documented judgment call, not a scientifically derived constant — see [docs/03-RISK-SCORING.md](03-RISK-SCORING.md) for the full math, the original 4-category weights before Regulatory was added, and the real bugs found and fixed while building the live news-spike layer.

---

## Beyond the 5 Scores: Three More Dashboard Sections

The Summary & Recommendations tab doesn't stop at the 5 category scores. Three more sections present the same underlying data from a different angle, each clearly labeled when it's a derived estimate rather than a directly measured number:

- **Supplier Risk** — the Supplier Concentration score restated, plus Single Source Dependency (how much of total sourcing comes from the single largest country) and Supplier Compliance Status, a real check of named suppliers (or the typed company name) against the US Treasury's Consolidated Screening List.
- **Logistics Risk** — Shipment Delays and Port Congestion (both real numbers derived from the existing route data), the Transportation Risk Index (the Logistics & Shipping score under a different name), and an On-Time Delivery Rate explicitly marked as an *estimate* — no free API publishes real carrier on-time statistics.
- **Geographic & External Risk** — three live NewsAPI keyword-spike checks (Natural Disaster Alerts, Weather Impact, Regional Conflict Alerts) against the top sourcing country, plus a Political/Regulatory Risks number that's just the Geopolitical and Regulatory scores averaged.

A **Dashboard Visualization** area follows: a Risk Ranking chart comparing all 11 industries at once (sorted by total score, broken into each category's real contribution), and a Trend Analysis chart that snapshots the current industry's score once a day and plots it over time as real history accumulates.

## Exporting the Report

Two buttons on the Summary tab generate the full report — every score, the AI summary, recommendations, and all the detail tables and charts above — as a downloadable **PDF or Excel file**, built with `fpdf2` and `openpyxl` respectively (`src/export.py`).

---

## What "Live Data" Actually Means

"Live" means different things for different data types:

| Data Type | How Live | Source |
|-----------|----------|--------|
| Commodity prices | Updated daily (cached 24h) | FRED API (Federal Reserve), Alpha Vantage |
| Shipping & Regulatory baselines | Hand-curated, updated every 1-2 weeks | Manual research |
| Shipping & Geopolitical & Regulatory "spike" layer | Refreshed daily | NewsAPI headline search |
| Natural Disaster / Weather / Regional Conflict alerts | Refreshed daily | NewsAPI headline search, new keyword sets |
| Geopolitical baseline | Updated annually (World Bank's own schedule) | World Bank governance indicators |
| Supplier concentration | Updated quarterly | Hand-researched |
| Supplier Compliance Status | Checked live, on demand | US Treasury Consolidated Screening List (via trade.gov) |

The structural data (which countries make which goods) updates slowly on purpose — that's realistic, since supply chain structure doesn't change overnight. The fast-moving layers (commodity prices, news-driven spikes) update daily so the dashboard reflects what's actually happening right now.

---

## The AI Layer — Why It's There

After calculating all the numbers, the app passes them to an LLM (**Groq's hosted Llama models when deployed, or a local Ollama model when running on your own machine** — not a paid API) to generate two things, shown in the **"Summary & Recommendations"** tab:

1. **A plain English risk brief** — 3-4 sentences translating the numbers into language a VP of Supply Chain could read in 10 seconds.
2. **Recommended actions** — the top 3 highest-risk categories, each paired with a specific, templated recommendation (e.g. "qualify backup suppliers" for high Supplier risk, "review tariff classifications" for high Regulatory risk).

This is how AI is used in real enterprise software — not to make the decisions, but to translate already-computed data into language humans can act on.

**If a company name is entered**, four more AI functions kick in:
- It detects which of the 11 industries the company belongs to and auto-syncs the dropdown.
- It estimates a small score adjustment per category based on real, named facts about that company (e.g. Apple's Foxconn relationship) — and explicitly does *nothing* if it isn't confident it recognizes the company, rather than inventing plausible-sounding details for a made-up name.
- For recognized companies, it lists their actual known sourcing countries (often more than the generic industry's 4-5) on the Geopolitical Map tab.
- It names real, specific suppliers (e.g. TSMC, Foxconn) when it has genuine knowledge of them, used for the High-Risk Suppliers and Supplier Compliance Status sections — falling back to the country-level sourcing breakdown when no specific suppliers are known.

**One important fix:** these functions originally had no fixed temperature or random seed, so the same company could get a different score on a different device or after the cache expired — a real bug, not just AI being "creative." Every function that produces a number or classification now runs with `temperature=0` and a fixed `seed`, so the same input always produces the same output regardless of where or when it's called. Prose-only output (the risk brief, recommendation wording) keeps natural variation since exact phrasing doesn't need to be identical every time.

---

## The Big Picture: How All the Pieces Connect

```
User picks an industry (or types a company name, which auto-detects its industry)
         ↓
Data layer fetches live data from FRED, Alpha Vantage, World Bank, NewsAPI, and trade.gov
         ↓
Risk model calculates 5 sub-scores (Supplier, Commodity, Logistics, Geopolitical, Regulatory) -
Commodity and Logistics as Probability x Impact x Current State, using per-industry weights
         ↓
If a recognized company was entered, AI nudges each sub-score based on real facts
         ↓
Streamlit builds the dashboard:
   - Real-time Critical Risk Alert banner
   - Gauge chart (total score) + 5 score cards + drill-down expander
   - Commodity price charts, shipping disruption panel, world map with supplier markers
   - Supplier Risk / Logistics Risk / Geographic & External Risk sections
   - Dashboard Visualization: Risk Ranking (all 11 industries) + Trend Analysis
         ↓
AI generates the Summary & Recommendations tab
         ↓
User sees the full risk picture in 5-10 seconds, or exports it as a PDF/Excel report
```

---

## What Makes This Impressive to Employers

1. **It's live** — any recruiter can open it, not just run on your laptop
2. **It's integrated** — 4 real data sources, not just one CSV file
3. **It's domain-relevant across 11 industries** — not just one narrow vertical
4. **It uses AI practically and honestly** — translating real computed data into language, with explicit guardrails against the AI fabricating company-specific "facts" it doesn't actually know
5. **It's deployed and iterated on** — you shipped something, gathered feedback, and revised the model (including reversing a feature after reviewing it) — which is exactly how real product work happens

Next: [docs/02-DATA-SOURCES.md](02-DATA-SOURCES.md) — The APIs, how to sign up, and what data each one gives you.
