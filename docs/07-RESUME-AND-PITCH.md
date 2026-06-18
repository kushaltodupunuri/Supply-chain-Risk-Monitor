# Resume, LinkedIn & Interview Pitch

This explains exactly how to present this project to get the maximum return from the work you've done.

---

## The Resume Bullet Points

### Short version (1 line, for tight resumes):

> **Supply Chain Risk Monitor** | Python, Streamlit, Plotly, REST APIs, LLMs | [live link]
> Live dashboard scoring real-time supply chain risk using commodity prices, shipping disruption data, live news signals, and AI-generated analysis across 11 industries, with one-click PDF/Excel export.

### Full version (3 bullets, when you have space):

> **Supply Chain Risk Monitor** | Python, Streamlit, Plotly, REST APIs, LLMs
> - Built a live web application that scores supply chain risk across 11 industries using a weighted, per-industry model across 5 categories (supplier concentration, commodity price risk modeled as Probability x Impact x Current State, logistics disruption, geopolitical exposure, regulatory/trade risk)
> - Integrated 6 real-time data sources (FRED, Alpha Vantage, World Bank, NewsAPI, Groq/Ollama LLMs, and the US Treasury's sanctions screening API via trade.gov) with disk-backed caching to stay within free-tier rate limits
> - Added a one-click PDF/Excel export of the full report (every score, AI summary, recommendations, and embedded charts/map), and a company-specific AI layer with explicit anti-hallucination guardrails — it says "not known" rather than inventing facts about an unrecognized or made-up company name
> - Deployed on Streamlit Cloud with zero paid dependencies anywhere in the stack; accessible at [your-link.streamlit.app]

### Which version to use when:

- **One-page resume with lots of experience:** Use the short version
- **Early career / internship target:** Use the full 3-bullet version — you need this to take up space and show depth
- **Senior role:** Use the short version and let them ask about it in the interview

---

## The LinkedIn Post (Copy-Paste Ready)

Post this when you deploy the app. Timing matters: post Tuesday-Thursday morning, 8-10am in your timezone.

---

**Option A — Data/Results-first version (performs better on LinkedIn):**

> The electronics supply chain is showing a 74/100 risk score right now.
>
> Here's why I built a tool to track this.
>
> After studying supply chain management, I kept noticing that the concepts we learned (supplier concentration, commodity hedging, geopolitical exposure) were all trackable in real time using public data. But nobody had built an easy dashboard to see them together.
>
> So I built one.
>
> The Supply Chain Risk Monitor pulls live data from FRED, Alpha Vantage, the World Bank, and live news signals, calculates a weighted risk score across 5 dimensions for 11 industries, and uses AI to translate the numbers into plain English — plus exports the full report to PDF or Excel in one click.
>
> Right now it shows:
> - Electronics at 51/100, driven mainly by supplier concentration (Taiwan semiconductor dependency)
> - Aerospace & Defense close behind, driven by export controls and a concentrated supplier base
> - The ranking shifts in real time as commodity prices and breaking news move
>
> Live app in the comments — would love feedback from supply chain professionals.
>
> #SupplyChain #Analytics #Python #DataScience #SupplyChainRisk

---

**Option B — Story/journey version:**

> 4 weeks ago I started building a supply chain risk tool in Python.
>
> Today I deployed it live.
>
> The idea: supply chain risk gets discussed in vague terms ("geopolitical uncertainty," "commodity headwinds"). I wanted to turn those concepts into a live, quantified dashboard.
>
> What I built:
> → Real-time commodity price tracking (FRED, Alpha Vantage APIs) plus a live news-spike layer for breaking disruptions
> → Weighted risk scoring model across 5 categories, 11 industries, with per-industry weight breakdowns
> → Interactive Plotly charts, a sourcing-risk world map, and a one-click PDF/Excel export of the full report
> → AI-generated plain English summary and company-specific analysis (Groq/Ollama, free) so any executive can understand it in 10 seconds
>
> Link in comments. Feedback welcome — especially from anyone who works in supply chain procurement or risk management.
>
> #SupplyChain #Python #Streamlit #DataAnalytics

---

**How to add the link on LinkedIn:**

Post the text first WITHOUT the link. After posting, add a comment that says "Live app: [your-url]" — LinkedIn's algorithm suppresses posts with external links in the caption. Putting it in the first comment avoids that.

---

## The Interview Pitch (2 Minutes)

This is what you say when a recruiter says "tell me about your projects."

**The script:**

> "I built a live supply chain risk monitor — it's a web app that anyone can open and use right now. You select one of 11 industries, like Electronics or Pharma, or type a specific company, and it immediately shows you a risk score from 0 to 100, broken into supplier concentration, commodity price risk, shipping disruption, geopolitical exposure, and regulatory risk. The data is live — it's pulling from the Federal Reserve, Alpha Vantage, the World Bank, live news for breaking disruptions, and even the US Treasury's sanctions list for supplier compliance checks. On top of the scores, there's an AI layer — running on free Groq/Ollama models, not a paid API — that writes a plain-English brief and, for recognized companies, names their actual real suppliers. You can export the whole thing to PDF or Excel in one click. I deployed it on Streamlit Cloud so it has a public URL. Do you want to see it?"

**Then open it on your phone or laptop and show them.**

The "do you want to see it?" close is the most important line. It turns a resume conversation into a product demonstration. Nobody else can do that.

---

## Recruiter-Specific Talking Points by Company

**For P&G, J&J, Pfizer (Consumer Goods / Pharma):**
> "I built in Pharma as one of the 11 industries because it has one of the most concentrated supply chains — about 70% of active pharmaceutical ingredients come from China and India, reflected directly in its supplier concentration score. The recommendations focus on supply base diversification to Ireland and Singapore."

**For Caterpillar, GM, Ford (Manufacturing / Automotive / Industrial Equipment):**
> "Automotive and Industrial Equipment & Machinery both track Steel, Copper, and Aluminum. The commodity score isn't just price trend — it's modeled as Probability x Impact x Current State: historical volatility, how much the price has already moved, and where today's price sits in its own recent range, combined via geometric mean so all three have to align for a high score, not just one outlier number."

**For Amazon, Target, Walmart (Retail / E-commerce):**
> "Retail scores are heavily influenced by ocean freight costs and Asia supplier concentration. I built the shipping disruption panel specifically because logistics was the #1 operational story of the past 3 years — Red Sea, Panama Canal, port strikes. The logistics risk score shows live status on each of those routes."

**For C.H. Robinson, XPO, Flexport, DHL (Logistics):**
> "The shipping section of the app is closest to what you do. I track each major lane — Red Sea, Panama Canal, US West Coast, US East Coast — with a disruption status, delay days, and cost premium. The logistics risk score is a weighted average across all routes by volume. I'd be curious whether the weights I used match how you think about lane importance."

---

## What to Put in Your GitHub README

Your GitHub README (the first thing people see when they visit your repo) should:

1. **Show a screenshot or GIF at the top.** Not a wall of text. A visual.
2. **State what it does in one line.**
3. **Link to the live app prominently.**
4. **List the data sources** — shows you did real research.
5. **Explain the scoring methodology briefly** — shows you understand the domain.
6. **Include setup instructions** — shows you can document.

**Sample README opening:**

```markdown
# Supply Chain Risk Monitor

Live web app → **[supply-chain-risk-monitor.streamlit.app](link)**

Scores real-time supply chain risk across 11 industries using commodity prices,
shipping disruption data, geopolitical indicators, and live news signals. Risk is
broken into 5 weighted dimensions (weights vary by industry): supplier concentration,
commodity price risk (modeled as Probability x Impact x Current State), logistics
disruption, geopolitical exposure, and regulatory/trade risk. Exports the full
report to PDF or Excel in one click.

![Dashboard screenshot](docs/screenshot.png)

## Data Sources
- [FRED (Federal Reserve)](https://fred.stlouisfed.org) — commodity prices, producer price indices
- [Alpha Vantage](https://alphavantage.co) — daily commodity prices
- [World Bank](https://data.worldbank.org) — country political stability indicators
- [NewsAPI](https://newsapi.org) — breaking-event spike detection
- [Groq](https://groq.com) / [Ollama](https://ollama.com) — free AI-generated risk summaries (no paid API anywhere in the stack)
- [trade.gov](https://developer.trade.gov) — US sanctions/compliance screening

## Risk Scoring Methodology
...
```

---

## The One-Line Self-Audit

Before you send any application, ask yourself:
*"If a recruiter spends 30 seconds on my resume, can they find the live URL and click it?"*

The URL should be:
- In the project description (not buried in a skills section)
- Clickable (hyperlinked in digital versions)
- Working (test it the day before any application)

If the answer to the audit is no, fix it before applying.

---

## What Comes After This

The company-specific analysis mode, PDF/Excel export, and several new dashboard sections (Supplier/Logistics/Geographic & External Risk, a Risk Ranking chart, score-trend tracking) all started as "what comes after this" ideas and are now live — see [PLAN.md](../PLAN.md) for the full history, including a couple of ideas that were built, shipped, and then deliberately reverted after review (an Executive Summary section, a Risk Heat Map). That's the actual lesson: ship the simple version, get real feedback, and let that feedback decide what's worth keeping.

Once you have real feedback from interviews or actual users, other directions worth considering:

- Industry-specific weight breakdowns for the other 10 industries (only Electronics has a customized weight set right now — see [docs/03-RISK-SCORING.md](../docs/03-RISK-SCORING.md))
- A "what changed this week" digest, now that score history is actually being tracked day over day
- Email alerts if a risk score crosses a threshold

But don't build any of that until you've shipped and used what you have. The first version deployed is worth more than the perfect version still in development.
