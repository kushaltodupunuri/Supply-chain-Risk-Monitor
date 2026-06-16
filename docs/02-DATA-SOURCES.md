# Data Sources — Every API Explained

This file explains every data source the app uses: what it is, why you need it, how to sign up, what the free tier gives you, and exactly what you call to get the data.

---

## Overview: What Data You Need

| Data Type | What It's For | Source |
|-----------|--------------|--------|
| Commodity prices (daily) | Commodity risk score + price charts | FRED API or Alpha Vantage |
| Country risk indicators | Geopolitical risk score + map | World Bank API |
| Trade flow data | Supplier concentration score | UN Comtrade API |
| Producer price indices | Commodity volatility calculation | BLS API |
| Shipping disruption status | Logistics risk score | Hand-coded + news flags |

---

## API #1: FRED (Federal Reserve Economic Data)

**What it is:** The Federal Reserve Bank of St. Louis publishes an enormous free database of economic data. This includes commodity prices, inflation indices, producer price indices, and hundreds of other indicators. Updated daily.

**Why you use it:** It's completely free with no hard rate limits. It's government data so it's reliable. It has commodity price history going back decades which you need for volatility calculations.

**How to sign up:**
1. Go to fred.stlouisfed.org
2. Click "My Account" → "Create Account"
3. After creating account, go to: fred.stlouisfed.org/docs/api/api_key.html
4. Click "Request API Key"
5. You get a key immediately. It's free, no credit card needed.

**What it gives you (free tier):**
- Unlimited API calls
- Thousands of economic series
- Daily price data with long history

**Key data series you will use:**

| Series ID | What It Is | Used For |
|-----------|-----------|----------|
| `WPUSI012011` | Steel producer price index | Automotive, Manufacturing risk |
| `PCOPPUSDM` | Copper price (monthly) | Automotive, Electronics risk |
| `PNGASEUUSDM` | Natural gas price | Energy-heavy industries |
| `PWHEAMTUSDM` | Wheat price | Food & Beverage risk |
| `PMAIZMTUSDM` | Corn price | Food & Beverage risk |
| `PSOYBUSDM` | Soybean price | Food & Beverage risk |
| `POILWTIUSDM` | Oil price (WTI crude) | Shipping cost driver |
| `LITHIUM` | Lithium price | EV/Automotive battery risk |

**How to call it in Python:**

```python
import requests

FRED_API_KEY = "your_key_here"  # Store in .env file

def get_fred_series(series_id, observation_start="2023-01-01"):
    url = "https://api.stlouisfed.org/fred/series/observations"
    params = {
        "series_id": series_id,
        "api_key": FRED_API_KEY,
        "file_type": "json",
        "observation_start": observation_start
    }
    response = requests.get(url, params=params)
    data = response.json()
    return data["observations"]  # List of {date, value} dicts
```

**Test call to verify it works:**
```python
# Run this to confirm your API key works
steel_prices = get_fred_series("WPUSI012011")
print(steel_prices[-5:])  # Last 5 data points
```

---

## API #2: Alpha Vantage

**What it is:** A financial data API that covers commodity prices, currency exchange rates, and some economic indicators. Better for daily commodity data than FRED in some cases.

**Why you use it:** FRED is monthly for many commodities. Alpha Vantage gives you daily prices, which is better for short-term trend calculations.

**How to sign up:**
1. Go to alphavantage.co
2. Click "Get Free API Key"
3. Fill out the form — no credit card needed
4. You get your API key immediately in your email

**What it gives you (free tier):**
- 25 API calls per day
- Daily commodity prices
- This is enough for development. In production you can cache results to stay under the limit.

**Key endpoints you will use:**

```python
# Copper (daily)
url = f"https://www.alphavantage.co/query?function=COPPER&interval=daily&apikey={ALPHA_KEY}"

# Aluminum (daily)
url = f"https://www.alphavantage.co/query?function=ALUMINUM&interval=daily&apikey={ALPHA_KEY}"

# Natural gas
url = f"https://www.alphavantage.co/query?function=NATURAL_GAS&interval=daily&apikey={ALPHA_KEY}"

# WTI Oil
url = f"https://www.alphavantage.co/query?function=WTI&interval=daily&apikey={ALPHA_KEY}"

# Wheat
url = f"https://www.alphavantage.co/query?function=WHEAT&interval=daily&apikey={ALPHA_KEY}"
```

**How to call it in Python:**

```python
import requests

ALPHA_KEY = "your_key_here"  # Store in .env file

def get_commodity_daily(commodity_function):
    url = "https://www.alphavantage.co/query"
    params = {
        "function": commodity_function,
        "interval": "daily",
        "apikey": ALPHA_KEY
    }
    response = requests.get(url, params=params)
    data = response.json()
    return data["data"]  # List of {date, value} dicts
```

**Important note about the free tier:** Alpha Vantage free tier allows 25 calls/day. Since you have multiple commodities to track, you will cache the results locally using Python's `functools.lru_cache` or just save them to a JSON file for the session. This is standard practice — even production apps cache API results.

---

## API #3: World Bank

**What it is:** The World Bank publishes hundreds of indicators for every country — political stability, governance quality, economic strength, infrastructure quality. This is what you use for your geopolitical risk scores.

**Why you use it:** It's completely free, no API key required, and it has a standardized "Political Stability and Absence of Violence" indicator that is perfect for your geopolitical risk score.

**How to sign up:** You don't need to. Just call it directly.

**Key indicators you will use:**

| Indicator Code | What It Measures |
|----------------|-----------------|
| `GOV_WGI_PV.EST` | Political Stability and Absence of Violence (−2.5 to +2.5) |
| `GOV_WGI_GE.EST` | Government Effectiveness |
| `GOV_WGI_CC.EST` | Control of Corruption |
| `GOV_WGI_RQ.EST` | Regulatory Quality |

**Note:** The short codes (`PV.EST`, etc.) you may see referenced elsewhere belong to an archived World Bank data source and will return "indicator not found" errors. Always use the `GOV_WGI_` prefixed codes, which point to the live, current dataset (World Bank source ID 3).

**How to call it in Python:**

```python
import requests

def get_country_risk(country_code, indicator="PV.EST"):
    # country_code examples: "CN" (China), "TW" (Taiwan), "IN" (India), "MX" (Mexico)
    url = f"https://api.worldbank.org/v2/country/{country_code}/indicator/{indicator}"
    params = {
        "format": "json",
        "mrv": 1  # Most recent value only
    }
    response = requests.get(url, params=params)
    data = response.json()
    # data[1] is the list of results
    return data[1][0]["value"]  # Returns the score
```

**Countries that matter by industry:**

| Industry | Key Countries to Track |
|----------|----------------------|
| Automotive | China (CN), Mexico (MX), Germany (DE), Japan (JP), South Korea (KR) |
| Electronics | Taiwan (TW), China (CN), South Korea (KR), Malaysia (MY), Vietnam (VN) |
| Pharma | China (CN), India (IN), Ireland (IE), Singapore (SG) |
| Retail | China (CN), Bangladesh (BD), Vietnam (VN), India (IN) |
| Food & Beverage | Brazil (BR), United States (US), Argentina (AR), Australia (AU), Ukraine (UA) |

---

## API #4: BLS (Bureau of Labor Statistics)

**What it is:** The US government's Bureau of Labor Statistics publishes Producer Price Indices (PPI) — these measure price changes at the wholesale level before goods reach consumers. This is better than retail prices for supply chain risk because you're measuring what manufacturers pay.

**Why you use it:** PPI data is more relevant to supply chain than consumer prices. If steel PPI is up 20%, a car manufacturer's costs go up even before they sell a single car.

**How to sign up:**
1. Go to bls.gov/developers
2. Click "Register" — you get an API key
3. Free tier allows 500 queries per day with a registered key

**How to call it in Python:**

```python
import requests
import json

BLS_API_KEY = "your_key_here"  # Store in .env file

def get_bls_series(series_id, start_year, end_year):
    url = "https://api.bls.gov/publicAPI/v2/timeseries/data/"
    headers = {"Content-type": "application/json"}
    data = json.dumps({
        "seriesid": [series_id],
        "startyear": str(start_year),
        "endyear": str(end_year),
        "registrationkey": BLS_API_KEY
    })
    response = requests.post(url, data=data, headers=headers)
    return response.json()["Results"]["series"][0]["data"]
```

**Key series IDs:**

| Series ID | What It Measures |
|-----------|-----------------|
| `WPU101` | Steel mill products PPI |
| `WPU102` | Iron and steel scrap PPI |
| `WPU102501` | Copper and copper products PPI |
| `WPU0652` | Plastics products PPI |
| `WPU061` | Pharmaceutical preparations PPI |

---

## API #5: Anthropic (Claude) — For AI Summary

**What it is:** The Claude API by Anthropic generates the plain English risk summary and recommendations panel in your app. You send it the risk scores and data, and it writes a business-appropriate summary.

**Why you use it over OpenAI:** Claude is better at following precise formatting instructions, which you need so the summary is always 3-4 sentences. Also, free tier is available.

**How to sign up:**
1. Go to console.anthropic.com
2. Create an account
3. Go to "API Keys" and create a key
4. Free tier: $5 in credits included when you sign up — enough for development

**How to call it in Python:**

```python
import anthropic

ANTHROPIC_KEY = "your_key_here"  # Store in .env file

client = anthropic.Anthropic(api_key=ANTHROPIC_KEY)

def generate_risk_summary(industry, scores, commodity_data):
    prompt = f"""
You are a supply chain risk analyst. Write a 3-4 sentence plain English summary of 
the current supply chain risk situation for the {industry} industry.

Current risk scores (0-100 scale, higher = more risk):
- Supplier Concentration Risk: {scores['supplier']}/100
- Commodity Price Risk: {scores['commodity']}/100
- Logistics & Shipping Risk: {scores['logistics']}/100
- Geopolitical Risk: {scores['geopolitical']}/100
- Overall Risk: {scores['total']}/100

Key commodity movements: {commodity_data}

Write as if briefing a supply chain executive. Be specific about the biggest risks.
Do not mention the scores directly. Translate them into business language.
"""
    
    message = client.messages.create(
        model="claude-haiku-4-5-20251001",  # Fast and cheap for summaries
        max_tokens=200,
        messages=[{"role": "user", "content": prompt}]
    )
    
    return message.content[0].text
```

---

## Shipping Disruption Data — The Special Case

Unlike the other data sources, shipping disruption data doesn't have a single clean free API. Here's what you do instead:

**Option A (Recommended): Curated static data with manual updates**

You create a Python dict that you update manually every week or two. This is completely legitimate — many professional risk dashboards do exactly this for qualitative data.

```python
# src/data/shipping.py

SHIPPING_STATUS = {
    "Red Sea / Suez Canal": {
        "status": "DISRUPTED",  # or "NORMAL" or "ELEVATED"
        "delay_days": 14,
        "cost_premium_pct": 40,
        "affected_trades": ["Asia-Europe", "Asia-Mediterranean"],
        "summary": "Houthi attacks causing rerouting around Cape of Good Hope since Dec 2023"
    },
    "Panama Canal": {
        "status": "ELEVATED",
        "delay_days": 3,
        "cost_premium_pct": 15,
        "affected_trades": ["Asia-East Coast US", "East Coast-West Coast"],
        "summary": "Drought reduced canal capacity; improved but not fully normal"
    },
    "US West Coast Ports": {
        "status": "NORMAL",
        "delay_days": 1,
        "cost_premium_pct": 5,
        "affected_trades": ["Trans-Pacific"],
        "summary": "Operating normally after 2023 labor agreement"
    },
    "US East Coast Ports": {
        "status": "NORMAL",
        "delay_days": 0,
        "cost_premium_pct": 0,
        "affected_trades": ["Trans-Atlantic", "South America"],
        "summary": "Operating normally"
    }
}
```

**Option B: Freightos Baltic Index (FBX)**
freightos.com/freightos-baltic-index/ publishes container shipping rates as an index. You can scrape the public data or use their API.

**Option C: Vessel Finder / Marine Traffic APIs**
These have free tiers and give you real vessel position data, but they're complex and overkill for this project.

**Recommendation: Start with Option A (static dict) and switch to Option B if you want to add live shipping cost data.**

---

## Setting Up Your .env File

Create a file called `.env` in your project root. Never commit this file to GitHub.

```
# .env — never commit this file
FRED_API_KEY=your_fred_key_here
ALPHA_VANTAGE_KEY=your_alpha_key_here
BLS_API_KEY=your_bls_key_here
ANTHROPIC_API_KEY=your_anthropic_key_here
```

Load it in Python:

```python
# At the top of any file that needs API keys
from dotenv import load_dotenv
import os

load_dotenv()  # Reads the .env file

FRED_API_KEY = os.getenv("FRED_API_KEY")
ALPHA_KEY = os.getenv("ALPHA_VANTAGE_KEY")
BLS_KEY = os.getenv("BLS_API_KEY")
ANTHROPIC_KEY = os.getenv("ANTHROPIC_API_KEY")
```

Add `.env` to your `.gitignore` file:
```
# .gitignore
.env
__pycache__/
*.pyc
```

---

## Caching Strategy

Because Alpha Vantage has a 25 calls/day limit and API calls slow down your app, you cache results.

Simple approach: cache to a local JSON file per session.

```python
import json
import os
from datetime import datetime

def get_with_cache(cache_key, fetch_function, cache_hours=6):
    cache_file = f"cache/{cache_key}.json"
    
    # Check if cached version is still fresh
    if os.path.exists(cache_file):
        with open(cache_file) as f:
            cached = json.load(f)
        cached_time = datetime.fromisoformat(cached["timestamp"])
        age_hours = (datetime.now() - cached_time).seconds / 3600
        if age_hours < cache_hours:
            return cached["data"]  # Return cached version
    
    # Otherwise fetch fresh
    data = fetch_function()
    os.makedirs("cache", exist_ok=True)
    with open(cache_file, "w") as f:
        json.dump({"timestamp": datetime.now().isoformat(), "data": data}, f)
    
    return data
```

Next: [docs/03-RISK-SCORING.md](03-RISK-SCORING.md) — Exactly how each 0-100 score is calculated.
