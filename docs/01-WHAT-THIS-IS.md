# What This App Is — Plain English Explanation

Read this first. It explains what you're building, why each part exists, and how the pieces connect. No jargon.

---

## The One-Line Description

You are building a website that looks at live real-world data — commodity prices, shipping news, geopolitical events — and turns it into a single risk score for a given industry's supply chain.

---

## What Problem Does It Solve?

Supply chain managers at companies like Apple, GM, or Pfizer spend hours every week trying to answer one question:

**"How exposed are we right now, and what's the biggest threat?"**

They have to check commodity prices (steel went up 15% last month), look at shipping news (Red Sea disruptions adding 3 weeks to Asia-Europe routes), read geopolitical reports (new US-China tariffs coming), and then somehow combine all of this into a clear picture.

Your app does that automatically, in seconds, for any industry.

---

## The Five Industries You Cover

You picked these because they have dramatically different supply chain profiles:

| Industry | Main Risks | Key Commodities |
|----------|-----------|-----------------|
| **Automotive** | Semiconductor shortage, raw material prices | Steel, aluminum, copper, lithium |
| **Pharma** | API sourcing from China/India, cold chain | Active pharmaceutical ingredients |
| **Electronics** | Taiwan semiconductor concentration, rare earths | Chips, rare earth metals, plastics |
| **Retail** | Ocean freight volatility, Asian manufacturing | Cotton, oil (shipping fuel), cardboard |
| **Food & Beverage** | Weather, agricultural commodities, fuel | Wheat, corn, soybeans, natural gas |

Each industry has different data sources and different risk weights. Electronics cares more about geopolitical risk (Taiwan). Food & Beverage cares more about commodity prices (crop harvests).

---

## The Four Risk Dimensions

Every supply chain has the same four categories of risk. Your app scores each one from 0-100.

### 1. Supplier Concentration Risk (30% of total score)

**What it means:** Are you buying from too few suppliers in too few countries?

If Apple buys 90% of its semiconductors from TSMC in Taiwan, and something happens in Taiwan, Apple has no backup. That's high concentration risk.

**How you measure it:** You use known industry data about where each industry sources from. Electronics scores very high on this because semiconductor manufacturing is concentrated in Taiwan and South Korea. Food & Beverage scores lower because agricultural production is globally distributed.

**This is 30% of the total** because sourcing concentration is the most fundamental supply chain risk — it determines how vulnerable you are to any disruption.

### 2. Commodity Price Risk (25% of total score)

**What it means:** Are the raw materials this industry needs spiking in price or becoming volatile?

If you make cars, you need steel. If steel prices jump 30% in a month, your production costs spike and you either lose margin or raise prices. If prices are volatile (swinging up and down unpredictably), that's also risky because you can't plan.

**How you measure it:** You pull live commodity price data from APIs and calculate two things:
- Price trend (is it going up recently?)
- Price volatility (is it swinging wildly?)

High trend + high volatility = high commodity risk score.

### 3. Logistics & Shipping Risk (25% of total score)

**What it means:** Can goods actually move from where they're made to where they're needed?

The Suez Canal / Red Sea situation in 2024-2025 added 2+ weeks to Asia-Europe shipping routes. The Panama Canal drought reduced capacity. West Coast port strikes caused delays. These events raise costs and cause shortages even when supply and demand are fine.

**How you measure it:** You track known disruption status of major routes. You score based on what percentage of global trade flows through disrupted routes and how severe the disruption is.

### 4. Geopolitical Risk (20% of total score)

**What it means:** Are there political tensions, trade wars, or sanctions that could cut off supply?

US-China tariffs affect electronics, rare earths, solar panels. Russia-Ukraine affects wheat, fertilizer, and energy. Taiwan Strait tensions affect semiconductors. These risks are hard to quantify but very real.

**How you measure it:** You use country risk indices (published by organizations like the World Bank) combined with industry-specific exposure data (how much of this industry's supply chain runs through high-risk countries).

---

## How the Score Is Calculated

You take each sub-score and apply a weighted average:

```
Total Risk Score = (Supplier × 0.30) + (Commodity × 0.25) + (Logistics × 0.25) + (Geopolitical × 0.20)
```

The weights reflect how much each factor contributes to actual supply chain failures historically.

See [docs/03-RISK-SCORING.md](03-RISK-SCORING.md) for the full math.

---

## What "Live Data" Actually Means

"Live" means different things for different data types:

| Data Type | How Live | Source |
|-----------|----------|--------|
| Commodity prices | Updated daily | FRED API (Federal Reserve), Alpha Vantage |
| Shipping disruptions | Updated manually with API flags | Public shipping data |
| Geopolitical risk | Updated quarterly | World Bank governance indicators |
| Supplier concentration | Updated annually | UN Comtrade, industry reports |

Commodity prices are the most live data. Supplier concentration changes slowly and you update it less frequently.

This means your app is showing *current market conditions* even if the underlying structural data (which countries make which goods) updates less often. That's fine and realistic — supply chain structure doesn't change overnight.

---

## The AI Summary — Why It's There

After calculating all the numbers, the app passes them to an AI (Claude, via the Anthropic API) with a prompt like:

> "Electronics industry risk scores: Supplier: 78, Commodity: 61, Logistics: 72, Geopolitical: 85. Current raw materials data: [data]. Write a 3-4 sentence plain English summary of the biggest risks right now."

The AI turns your numbers into a readable business brief. A recruiter or executive can read it in 10 seconds and understand the situation without knowing what any of the scores mean.

This is how AI is used in real enterprise software — not to make the decisions, but to translate data into language that humans can act on.

---

## The Recommendations Panel — How It Works

This is also AI-generated but it's templated. You give the AI the scores and it selects from a library of pre-researched recommendations that are relevant to the risk levels.

For example:
- If Electronics geopolitical risk > 70: recommend diversifying semiconductor sourcing to Vietnam or India
- If Logistics risk > 60: recommend evaluating air freight for time-sensitive components
- If Commodity risk > 65: recommend futures contracts or longer-term supplier agreements to lock in prices

The AI writes these in natural language so they sound thoughtful, not like canned responses.

---

## The Big Picture: How All the Pieces Connect

```
User picks industry (Electronics)
         ↓
Data layer fetches live data from 4-5 APIs
         ↓
Risk model calculates 4 sub-scores
         ↓
Streamlit builds the dashboard:
   - Gauge chart (total score)
   - Score cards (4 sub-scores)
   - Commodity price charts
   - Shipping disruption panel
   - World map
         ↓
AI generates summary + recommendations
         ↓
User sees full risk picture in 5-10 seconds
```

---

## What Makes This Impressive to Employers

1. **It's live** — any recruiter can open it, not just run on your laptop
2. **It's integrated** — multiple data sources, not just one CSV file
3. **It's domain-relevant** — you understand the actual risk categories that supply chain managers care about
4. **It uses AI practically** — not "I used ChatGPT," but "I integrated an LLM API to translate structured data into business language"
5. **It's deployed** — you shipped something, which most analysts never do

Next: [docs/02-DATA-SOURCES.md](02-DATA-SOURCES.md) — The APIs, how to sign up, and what data each one gives you.
