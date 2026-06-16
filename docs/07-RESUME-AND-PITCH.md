# Resume, LinkedIn & Interview Pitch

This explains exactly how to present this project to get the maximum return from the work you've done.

---

## The Resume Bullet Points

### Short version (1 line, for tight resumes):

> **Supply Chain Risk Monitor** | Python, Streamlit, Plotly, REST APIs | [live link]
> Live dashboard scoring real-time supply chain risk using commodity prices, shipping disruption data, and AI-generated analysis across 5 industries.

### Full version (3 bullets, when you have space):

> **Supply Chain Risk Monitor** | Python, Streamlit, Plotly, REST APIs
> - Built a live web application that scores supply chain risk across 5 industries using a weighted model across supplier concentration, commodity price volatility, shipping disruptions, and geopolitical exposure
> - Integrated 4 real-time data APIs (FRED Federal Reserve, Alpha Vantage, World Bank) to surface commodity price trends and country-level risk indicators with daily refresh
> - Deployed on Streamlit Cloud with AI-generated (Claude API) plain-English risk summaries and actionable recommendations; accessible at [your-link.streamlit.app]

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
> The Supply Chain Risk Monitor pulls live data from FRED (Federal Reserve), Alpha Vantage, and the World Bank, calculates a weighted risk score across 4 dimensions, and uses AI to translate the numbers into plain English.
>
> Right now it shows:
> - Electronics at 74/100 (Taiwan semiconductor concentration + elevated copper prices)
> - Food & Beverage at 48/100 (globally diversified agricultural base)
> - Pharma at 69/100 (heavy API ingredient sourcing from China and India)
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
> → Real-time commodity price tracking (FRED, Alpha Vantage APIs)
> → Weighted risk scoring model (supplier concentration, commodity volatility, logistics, geopolitics)
> → Interactive Plotly charts and world map
> → AI-generated plain English summary (Claude API) so any executive can understand it in 10 seconds
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

> "I built a live supply chain risk monitor — it's a web app that anyone can open and use right now. You select an industry, like Electronics or Pharma, and it immediately shows you a risk score from 0 to 100, broken into supplier concentration, commodity price risk, shipping disruption, and geopolitical exposure. The data is live — it's pulling from the Federal Reserve's commodity price database, Alpha Vantage for daily prices, and the World Bank for country risk indicators. On top of the scores, there's an AI layer that takes all the numbers and writes a 3-4 sentence brief that a VP of Supply Chain could read in 10 seconds to understand what's happening right now. I deployed it on Streamlit Cloud so it has a public URL. Do you want to see it?"

**Then open it on your phone or laptop and show them.**

The "do you want to see it?" close is the most important line. It turns a resume conversation into a product demonstration. Nobody else can do that.

---

## Recruiter-Specific Talking Points by Company

**For P&G, J&J, Pfizer (Consumer Goods / Pharma):**
> "I built in Pharma as one of the five industries because it has the most concentrated supply chain — about 70% of active pharmaceutical ingredients come from China and India. The geopolitical risk score for Pharma reflects that directly, and the recommendations focus on supply base diversification to Ireland and Singapore."

**For Caterpillar, GM, Ford (Manufacturing / Automotive):**
> "The Automotive module tracks steel, aluminum, and lithium — the three commodities that move your margins. I built the commodity risk score to weight price trend more heavily than volatility because a sustained rise is more damaging than a spike you can hedge."

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

Scores real-time supply chain risk across 5 industries using commodity prices, 
shipping disruption data, and geopolitical indicators. Risk is broken into 4 
weighted dimensions: supplier concentration (30%), commodity price volatility (25%), 
logistics disruption (25%), and geopolitical exposure (20%).

![Dashboard screenshot](docs/screenshot.png)

## Data Sources
- [FRED (Federal Reserve)](https://fred.stlouisfed.org) — commodity prices, producer price indices
- [Alpha Vantage](https://alphavantage.co) — daily commodity prices
- [World Bank](https://data.worldbank.org) — country political stability indicators
- [Anthropic Claude](https://anthropic.com) — AI-generated risk summaries

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

Once you have the app live and you've been using it in interviews for a few months, you'll have real feedback on what people want to see. At that point, consider:

- Adding a company-specific analysis mode (scrapes public filing data for specific companies)
- Adding a "what changed this week" digest
- Adding email alerts if risk scores cross thresholds

But don't build any of that until you've shipped and used what you have. The first version deployed is worth more than the perfect version still in development.
