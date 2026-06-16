# Supply Chain Risk Monitor

A live, interactive web application that scores real-time supply chain risk across 5 industries using commodity prices, shipping disruption data, and geopolitical indicators.

**Live App:** `[your-app-name].streamlit.app` *(URL generated after deployment)*
**Built with:** Python, Streamlit, Plotly, REST APIs

---

## What This App Does (30-Second Version)

A user opens the app, picks an industry (like Electronics or Pharma), and instantly sees:
- A single risk score from 0 to 100
- Broken into 4 sub-scores (suppliers, prices, shipping, geopolitics)
- Live commodity price charts
- Shipping route disruption alerts
- A world map showing sourcing risk by country
- An AI-written plain English summary of the biggest risks right now
- 3 specific recommendations

---

## Folder Structure

```
Supply-Chain-Risk-Monitor/
├── README.md                    ← You are here. The big picture.
├── PLAN.md                      ← Week-by-week build plan
├── app.py                       ← The main Streamlit app (entry point)
│
├── docs/
│   ├── 01-WHAT-THIS-IS.md       ← Plain English explanation of the whole app
│   ├── 02-DATA-SOURCES.md       ← Every API used and why, with free signup links
│   ├── 03-RISK-SCORING.md       ← Exactly how the 0-100 score is calculated
│   ├── 04-BUILDING-THE-UI.md    ← How Streamlit works and how to build the dashboard
│   ├── 05-AI-SUMMARY.md         ← How the AI-generated risk summary works
│   ├── 06-DEPLOYMENT.md         ← How to put it live on the internet for free
│   └── 07-RESUME-AND-PITCH.md   ← How to present this on your resume and LinkedIn
│
└── src/
    ├── data/                    ← Code for fetching data from APIs
    ├── models/                  ← Code for calculating risk scores
    └── ui/                      ← Code for each section of the dashboard
```

---

## Start Here

If you are new to this project, read the docs in this order:

1. [docs/01-WHAT-THIS-IS.md](docs/01-WHAT-THIS-IS.md) — Understand what you're building
2. [docs/02-DATA-SOURCES.md](docs/02-DATA-SOURCES.md) — Sign up for APIs, understand the data
3. [docs/03-RISK-SCORING.md](docs/03-RISK-SCORING.md) — Understand the math/logic
4. [docs/04-BUILDING-THE-UI.md](docs/04-BUILDING-THE-UI.md) — Build the web app
5. [docs/05-AI-SUMMARY.md](docs/05-AI-SUMMARY.md) — Add the AI layer
6. [docs/06-DEPLOYMENT.md](docs/06-DEPLOYMENT.md) — Put it live
7. [docs/07-RESUME-AND-PITCH.md](docs/07-RESUME-AND-PITCH.md) — Use it to get hired
8. [PLAN.md](PLAN.md) — Track your weekly progress

---

## Quick Start (Once You Have API Keys)

```bash
# 1. Install dependencies
pip install streamlit plotly pandas requests anthropic python-dotenv

# 2. Create a .env file with your API keys (see docs/02-DATA-SOURCES.md)

# 3. Run locally
streamlit run app.py

# 4. Deploy online (free)
streamlit deploy app.py
```

---

## Why This Project Works for Your Resume

- It is a **live URL** recruiters can click — not a PDF or notebook
- It covers **commodity risk, logistics, geopolitics** — relevant to every supply chain team
- It shows **real-time data skills** — not just historical analysis
- It uses **AI** in a practical, professional way
- It is **deployed** — meaning you followed the project through to completion

See [docs/07-RESUME-AND-PITCH.md](docs/07-RESUME-AND-PITCH.md) for exact resume bullet points and LinkedIn copy.
