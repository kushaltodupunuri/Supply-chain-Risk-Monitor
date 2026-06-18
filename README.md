# SupplyIQ

A live, interactive web application with two parts under one sidebar: **Risk Monitor**, which scores real-time supply chain risk across **11 industries** (or a specific company, if recognized) using commodity prices, shipping disruption data, geopolitical indicators, trade-policy news, and a US sanctions screening check; and **6 SupplyIQ modules** that help a small business simulate, forecast, and optimize its own day-to-day supply chain from data it enters or uploads. Both share an AI layer (Risk Monitor) or transparent, adjustable-assumption math (SupplyIQ modules) that turns numbers into plain-English analysis.

---

## What This App Does (30-Second Version)

**Risk Monitor** — a user picks an industry (like Electronics or Pharma) or types a company name, and sees:
- A single risk score from 0 to 100, broken into 5 weighted categories (Supplier Concentration, Commodity Price, Logistics & Shipping, Geopolitical, Regulatory & Trade)
- A real-time critical-risk alert banner, live commodity price charts, a shipping-route status panel, and a sourcing-risk world map with supplier-location markers
- Supplier Risk (compliance screening, single-source dependency), Logistics Risk (shipment delays, port congestion), and Geographic & External Risk (live disaster/weather/conflict news alerts) breakdowns
- A Dashboard Visualization area ranking all 11 industries by risk and tracking the current industry's score trend over time
- An AI-written plain-English summary, 3 recommendations, and (for recognized companies) real named suppliers and sourcing countries
- A one-click export of the full report to **PDF or Excel**, and a dark mode toggle

**SupplyIQ modules** — 6 additional sidebar pages aimed at a small business managing its own operations, each working from data the user enters or uploads (not live external feeds):
- **Supply Chain Simulator** — 5 questions → a visual flow diagram of your supply chain with heuristic health scoring
- **Demand Forecasting Engine** — upload sales history (or use demo data) → 3 forecasting models, seasonal/stockout/overstock alerts
- **Supplier Performance Scorecard** — grade your suppliers A-F and estimate the cost of the worst ones
- **Logistics & Route Optimizer** — compare carrier costs by destination, find shipment-consolidation savings
- **Cost Optimization Engine** — pulls data from the two pages above to total up monthly savings opportunities
- **Executive Dashboard** — all of the above on one screen, with prioritized action items

---

## Folder Structure

```
Supply-Chain-Risk-Monitor/
├── README.md                    ← You are here. The big picture.
├── Risk_Monitor.py              ← The Risk Monitor entry point (main Streamlit script)
├── requirements.txt             ← Python dependencies
├── packages.txt                 ← System (apt) packages Streamlit Cloud needs for kaleido/Chrome
│
├── pages/                       ← The 6 SupplyIQ modules (Streamlit auto-discovers these as
│   ├── 1_Supply_Chain_Simulator.py    sidebar pages alongside Risk_Monitor.py)
│   ├── 2_Demand_Forecasting.py
│   ├── 3_Supplier_Scorecard.py
│   ├── 4_Logistics_Route_Optimizer.py
│   ├── 5_Cost_Optimization.py
│   └── 6_Executive_Dashboard.py
│
├── docs/
│   ├── 01-WHAT-THIS-IS.md       ← Plain English explanation of the whole app
│   ├── 02-DATA-SOURCES.md       ← Every API used and why, with free signup links
│   ├── 03-RISK-SCORING.md       ← Exactly how the 0-100 score is calculated
│   ├── 04-BUILDING-THE-UI.md    ← How Streamlit works and how the dashboard is built
│   ├── 05-AI-SUMMARY.md         ← How the AI-generated risk summary works (Groq/Ollama)
│   ├── 06-DEPLOYMENT.md         ← How to put it live on the internet for free
│   └── 07-RESUME-AND-PITCH.md   ← How to present this on your resume and LinkedIn
│
└── src/
    ├── config.py                ← Reads API keys from Streamlit secrets or .env
    ├── charts.py                ← Shared Plotly figure builders (used by both the app and exports)
    ├── export.py                ← Builds the full PDF/Excel report
    ├── ui_helpers.py             ← Shared card/CSS styling used by the 6 SupplyIQ module pages
    ├── data/                    ← Code for fetching data from APIs (commodities, geopolitical,
    │                               shipping, news alerts, sanctions screening, score history)
    ├── models/                  ← Code for calculating each risk category's score
    └── ai/                      ← Groq/Ollama-backed summary, recommendations, and
                                     company-specific functions
```

---

## Start Here

If you are new to this project, read the docs in this order:

1. [docs/01-WHAT-THIS-IS.md](docs/01-WHAT-THIS-IS.md) — Understand what you're building
2. [docs/02-DATA-SOURCES.md](docs/02-DATA-SOURCES.md) — Sign up for APIs, understand the data
3. [docs/03-RISK-SCORING.md](docs/03-RISK-SCORING.md) — Understand the math/logic
4. [docs/04-BUILDING-THE-UI.md](docs/04-BUILDING-THE-UI.md) — How the dashboard is built
5. [docs/05-AI-SUMMARY.md](docs/05-AI-SUMMARY.md) — The AI layer
6. [docs/06-DEPLOYMENT.md](docs/06-DEPLOYMENT.md) — Put it live
7. [docs/07-RESUME-AND-PITCH.md](docs/07-RESUME-AND-PITCH.md) — Use it to get hired
8. [PLAN.md](PLAN.md) — The full history of what was built and why, including features added then reverted

---

## Quick Start (Once You Have API Keys)

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Create a .env file with your API keys (see docs/02-DATA-SOURCES.md)
#    Required: FRED_API_KEY, ALPHA_VANTAGE_KEY, NEWS_API_KEY
#    Optional: GROQ_API_KEY (falls back to local Ollama if not set),
#              TRADE_GOV_API_KEY (Supplier Compliance Status shows "not checked" without it)

# 3. Run locally
streamlit run Risk_Monitor.py
#    (the 6 SupplyIQ modules in pages/ need no API keys - they work from data you
#    enter or upload, and appear automatically in the sidebar)

# 4. Deploy online (free) - push to GitHub and connect the repo at share.streamlit.io
#    (packages.txt is already set up for the apt dependencies kaleido needs there)
```

---
