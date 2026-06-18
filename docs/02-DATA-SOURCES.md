# Data Sources — Every API Explained

This file explains every data source the live app actually uses: what it is, why it's there, how to sign up, what the free tier gives you, and where it's called in the code.

**This doc was rewritten to match the live app.** The original plan also called for BLS (Bureau of Labor Statistics), UN Comtrade, and Anthropic's Claude API. None of those made it into the final build — BLS and UN Comtrade turned out to be redundant with what FRED and Alpha Vantage already provide, and Claude was swapped for Groq/Ollama (see below) specifically so the project has **no paid dependency anywhere in the stack**. The six sources below are what's actually wired up.

---

## Overview: What Data You Need

| Data Type | What It's For | Source |
|-----------|--------------|--------|
| Commodity prices | Commodity Price risk score + price charts | FRED API, Alpha Vantage |
| Country risk indicators | Geopolitical risk score + sourcing map | World Bank API |
| Breaking-event signals | The "spike" layer on top of Logistics, Geopolitical, Regulatory, and the new Geographic & External Risk alerts | NewsAPI |
| AI summary, recommendations, company-specific facts | The Summary & Recommendations tab | Groq (deployed) / Ollama (local) |
| Sanctions/compliance screening | Supplier Compliance Status | trade.gov Consolidated Screening List |
| Shipping disruption status | Logistics & Shipping risk score | Hand-curated (`src/data/shipping.py`) + the NewsAPI spike layer |

---

## API #1: FRED (Federal Reserve Economic Data)

**File:** `src/data/commodity_prices.py`

**What it is:** The Federal Reserve Bank of St. Louis publishes a free database of economic data, including producer price indices going back decades.

**Why you use it:** No rate limit, government-reliable, and it's the only free source for two commodities Alpha Vantage doesn't cover: Steel and Titanium.

**How to sign up:**
1. Go to fred.stlouisfed.org → "My Account" → "Create Account"
2. Go to fred.stlouisfed.org/docs/api/api_key.html → "Request API Key"
3. You get a key immediately, free, no credit card.

**Series actually used:**

| Series ID | What It Is | Frequency |
|-----------|-----------|-----------|
| `WPUSI012011` | Steel producer price index | Monthly |
| `WPU102505` | Titanium producer price index | Monthly |

**How it's called:**

```python
url = "https://api.stlouisfed.org/fred/series/observations"
params = {"series_id": series_id, "api_key": FRED_API_KEY, "file_type": "json", "observation_start": start_date}
response = requests.get(url, params=params, timeout=15)
```

---

## API #2: Alpha Vantage

**File:** `src/data/commodity_prices.py`

**What it is:** A financial data API covering commodity prices and more.

**Why you use it:** Covers the other 7 tracked commodities (Copper, Aluminum, Oil/WTI, Natural Gas, Wheat, Corn, Cotton) that FRED's free tier doesn't have as clean monthly/daily series.

**How to sign up:**
1. Go to alphavantage.co → "Get Free API Key"
2. No credit card needed — the key arrives immediately by email.

**Free tier limit:** 5 calls/minute, 25/day on some plans. The code enforces a 13-second gap between calls (`_ALPHA_MIN_GAP_SECONDS`) to stay under the per-minute limit, and caches every result to disk for 24 hours so a normal session makes very few live calls.

**Real data quirk to know about:** Oil and Natural Gas come back as true daily prices. Copper, Aluminum, Wheat, Corn, and Cotton are **monthly** on the free tier. Naively taking "the last 90 entries" would span 7+ years for the monthly ones instead of 90 days — `_filter_to_window()` filters by actual calendar date before any trend/volatility math runs, regardless of how many raw entries came back.

---

## API #3: World Bank

**File:** `src/data/geopolitical.py`

**What it is:** Free, no API key, with a standardized "Political Stability and Absence of Violence" indicator per country — exactly what the Geopolitical score needs.

**Indicator actually used:** `GOV_WGI_PV.EST` (−2.5 worst to +2.5 best). **Real bug found and fixed:** the shorter code you might see referenced elsewhere (`PV.EST`) points to an archived data source and silently returns "indicator not found." The live, current code is the `GOV_WGI_`-prefixed one (World Bank source ID 3).

```python
url = f"https://api.worldbank.org/v2/country/{country_code}/indicator/GOV_WGI_PV.EST"
params = {"format": "json", "mrv": 5}  # looks back up to 5 years for the most recent non-null value
```

Cached 7 days, since World Bank only updates this annually.

---

## API #4: NewsAPI

**File:** `src/data/news_alerts.py`

**What it is:** A headline-search API used as the "fast alert layer" sitting on top of every slow-moving baseline (route status, World Bank scores, regulatory baselines) — it catches a breaking event between manual/annual updates.

**How to sign up:** newsapi.org → free Developer plan, no credit card.

**Free tier limit:** 100 requests/24h (50 every 12h). Every subject is cached 24h, and the comparison is a **ratio** (this week's mentions vs. the subject's own 30-day baseline rate), not a raw count — a naturally newsworthy country like China always has thousands of mentions, while a quiet one like Vietnam might have a handful; comparing each subject to its own baseline is what lets a genuine spike stand out for either.

**Used by four different keyword sets**, all going through the same `get_relative_alert()` function:
- `RISK_KEYWORDS` — Logistics & Geopolitical (tariff, sanctions, strike, conflict, war, blockade...)
- `REGULATORY_KEYWORDS` — Regulatory & Trade (tariff, trade war, export control, import ban...)
- `NATURAL_DISASTER_KEYWORDS` / `WEATHER_KEYWORDS` / `CONFLICT_KEYWORDS` — the Geographic & External Risk section's three alerts (earthquake/flood/hurricane..., drought/storm/heatwave..., war/coup/civil unrest...)

**Real bugs found and fixed here** (worth knowing if you extend this file): headline-only search (`qInTitle`, not full-text `q`) to avoid false positives from unrelated body text; multi-word keywords must be quoted individually or NewsAPI splits them into separate OR'd words (`"export ban"` unquoted once matched bare "ban" in cricket headlines); a `MIN_RECENT_COUNT_FOR_ALERT` guardrail so a quiet subject's 1-article baseline jumping to 4 articles doesn't look like a 300% spike off pure sample noise.

---

## API #5: Groq (deployed) / Ollama (local)

**Files:** `src/ai/summary.py`

**What it is:** Two free LLM providers behind one shared `_call_llm()` function — **Groq's hosted API** (free tier, used once deployed to Streamlit Cloud) when `GROQ_API_KEY` is set, otherwise **a local Ollama model** (no key needed, runs entirely on your machine during development).

**Why two providers instead of one:** Streamlit Cloud can't run Ollama (it needs a local model server), and requiring every contributor to get a paid API key just to run the app locally is unnecessary friction. This way the whole stack — including the AI layer — has zero paid dependencies.

**How to sign up for Groq:** console.groq.com → free account → API Keys → create one. No credit card.

**How to set up Ollama locally:** ollama.com → install → `ollama pull llama3.2` → it runs as a local background service; the code just calls `ollama.chat(model="llama3.2", ...)`.

**What it's used for:**
- The risk brief and recommendation detail text (prose, default sampling)
- Company industry detection, score adjustment, sourcing-country list, and named-supplier list (all run with `temperature=0` and a fixed `seed` — see [docs/05-AI-SUMMARY.md](05-AI-SUMMARY.md) for why this matters and what bug it fixed)

---

## API #6: trade.gov Consolidated Screening List

**File:** `src/data/sanctions.py`

**What it is:** The US government's official, free API for screening a name against OFAC's Specially Designated Nationals list and several other restricted-party lists. Backs the Supplier Compliance Status metric.

**How to sign up:**
1. developer.trade.gov → "Sign in" → "Sign up now" (new portal — an old trade.gov developer account won't carry over)
2. Go to Products → "Data Services Platform APIs" → Subscribe (any subscription name)
3. Your Profile page shows a Primary/Secondary key — either works as `TRADE_GOV_API_KEY`

**Real bug found and fixed:** the *direct* OFAC SDN.CSV download (the older, simpler approach) is served from a host with a broken certificate chain — it loads fine in a browser (Windows tolerates the broken chain more leniently) but fails standard Python/Linux TLS verification, which would also fail on Streamlit Cloud. The trade.gov API is the modern, correctly-configured replacement.

**Real false positive found and fixed:** the first matching approach (whole-word substring match) flagged "Apple" as a match against "ORIENTAL APPLE COMPANY PTE LTD" — a real company name innocently containing the word "Apple." Fixed by requiring an **exact** name match (case/whitespace-insensitive) instead, trading recall for not flagging real companies incorrectly.

If `TRADE_GOV_API_KEY` isn't set, Supplier Compliance Status honestly shows "Not checked" rather than a false "Clear."

---

## Shipping Disruption Data — Hand-Curated by Design

**File:** `src/data/shipping.py`

No free API publishes a continuously-updated, structured "is this shipping route disrupted right now" feed. The app uses a hand-curated dict instead, updated every 1-2 weeks based on current shipping news — the same legitimate approach many professional risk dashboards use for qualitative data:

```python
SHIPPING_STATUS = {
    "Red Sea / Suez Canal": {
        "status": "DISRUPTED",
        "delay_days": 14,
        "cost_premium_pct": 40,
        "affected_trades": ["Asia-Europe", "Asia-Mediterranean"],
        "summary": "Houthi attacks causing rerouting around Cape of Good Hope since Dec 2023",
    },
    # Panama Canal, US West/East Coast Ports, Strait of Malacca...
}
```

The NewsAPI spike layer (`get_route_alert`) sits on top of this, catching a sudden event the manual update hasn't caught up to yet.

---

## Setting Up Your .env File

```
# .env — never commit this file
FRED_API_KEY=your_fred_key
ALPHA_VANTAGE_KEY=your_alpha_vantage_key
NEWS_API_KEY=your_newsapi_key
GROQ_API_KEY=your_groq_key
TRADE_GOV_API_KEY=your_trade_gov_key
```

`GROQ_API_KEY` and `TRADE_GOV_API_KEY` are optional — the app falls back to local Ollama and an honest "not checked" status respectively if they're missing.

`src/config.py`'s `get_secret()` reads from Streamlit's `st.secrets` first (for the deployed app), falling back to this `.env` file (for local development) — the same function call works in both places:

```python
def get_secret(key):
    try:
        import streamlit as st
        if key in st.secrets:
            return st.secrets[key]
    except Exception:
        pass
    return os.getenv(key)
```

`.gitignore` already excludes `.env` and the `cache/` directory (where the file-based caches below live).

---

## Caching Strategy

Every external call (FRED, Alpha Vantage, World Bank, NewsAPI, and the daily score-history snapshot) caches its result to a local JSON file under `cache/`, keyed by subject and TTL — the same pattern repeated across `src/data/*.py`:

```python
def _read_cache(key, max_age_hours=24):
    if not os.path.exists(path):
        return None
    cached = json.load(open(path))
    age_hours = (datetime.now() - datetime.fromisoformat(cached["timestamp"])).total_seconds() / 3600
    return cached["data"] if age_hours < max_age_hours else None

def _write_cache(key, data):
    json.dump({"timestamp": datetime.now().isoformat(), "data": data}, open(path, "w"))
```

Cache windows are tuned per source: commodity prices 24h (1h for a cached *failure*, so a rate-limited API doesn't get hammered every page load but also recovers quickly), World Bank 7 days (matches their annual update cadence), NewsAPI 24h per subject.

**Note for Streamlit Cloud:** this cache lives on the app's local filesystem, which is only persistent for the container's lifetime — a redeploy or a free-tier sleep/wake cycle can reset it. That's fine for this use case (it just means a fresh fetch on the next page load), but it's worth knowing if you're wondering why "yesterday's" cached data isn't there after a redeploy.

Next: [docs/03-RISK-SCORING.md](03-RISK-SCORING.md) — Exactly how each 0-100 score is calculated.
