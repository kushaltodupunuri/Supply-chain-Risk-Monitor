import os
import json
import time
from datetime import datetime, timedelta
import requests

from src.config import get_secret

_LAST_ALPHA_CALL = 0
_ALPHA_MIN_GAP_SECONDS = 13  # Free tier allows 5 calls/minute; this keeps us safely under that

FRED_API_KEY = get_secret("FRED_API_KEY")
ALPHA_VANTAGE_KEY = get_secret("ALPHA_VANTAGE_KEY")

CACHE_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "cache")

COMMODITY_SOURCE_MAP = {
    "Steel": {"source": "fred", "id": "WPUSI012011"},
    "Copper": {"source": "alpha", "function": "COPPER"},
    "Aluminum": {"source": "alpha", "function": "ALUMINUM"},
    "Oil (WTI)": {"source": "alpha", "function": "WTI"},
    "Natural Gas": {"source": "alpha", "function": "NATURAL_GAS"},
    "Wheat": {"source": "alpha", "function": "WHEAT"},
    "Corn": {"source": "alpha", "function": "CORN"},
    "Cotton": {"source": "alpha", "function": "COTTON"},
    # FRED PPI series, like Steel - monthly data, same caveat applies.
    "Titanium": {"source": "fred", "id": "WPU102505"},
}

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


def _cache_path(commodity_name):
    safe_name = commodity_name.replace(" ", "_").replace("(", "").replace(")", "")
    return os.path.join(CACHE_DIR, f"{safe_name}.json")


def _read_cache(commodity_name, max_age_hours=24, failure_max_age_hours=1):
    """A cached failure (empty list) expires much faster than a real cached price
    history - this stops the app from retrying the same doomed, rate-limited API
    call on every single page reload, while still recovering automatically within
    about an hour without needing a restart.
    """
    path = _cache_path(commodity_name)
    if not os.path.exists(path):
        return None
    with open(path) as f:
        cached = json.load(f)
    age_hours = (datetime.now() - datetime.fromisoformat(cached["timestamp"])).total_seconds() / 3600
    effective_max_age = failure_max_age_hours if cached.get("is_failure") else max_age_hours
    return cached["data"] if age_hours < effective_max_age else None


def _write_cache(commodity_name, data, is_failure=False):
    os.makedirs(CACHE_DIR, exist_ok=True)
    with open(_cache_path(commodity_name), "w") as f:
        json.dump({"timestamp": datetime.now().isoformat(), "data": data, "is_failure": is_failure}, f)


def _fetch_fred(series_id, days=90):
    start_date = (datetime.now() - timedelta(days=days * 3)).strftime("%Y-%m-%d")
    url = "https://api.stlouisfed.org/fred/series/observations"
    params = {
        "series_id": series_id,
        "api_key": FRED_API_KEY,
        "file_type": "json",
        "observation_start": start_date,
    }
    response = requests.get(url, params=params, timeout=15)
    response.raise_for_status()
    observations = response.json()["observations"]
    cleaned = [
        {"date": o["date"], "value": float(o["value"])}
        for o in observations
        if o["value"] != "."
    ]
    return cleaned[-days:]


def _fetch_alpha(function_name, days=90):
    global _LAST_ALPHA_CALL
    elapsed = time.time() - _LAST_ALPHA_CALL
    if elapsed < _ALPHA_MIN_GAP_SECONDS:
        time.sleep(_ALPHA_MIN_GAP_SECONDS - elapsed)
    _LAST_ALPHA_CALL = time.time()

    url = "https://www.alphavantage.co/query"
    params = {
        "function": function_name,
        "interval": "daily",
        "apikey": ALPHA_VANTAGE_KEY,
    }
    response = requests.get(url, params=params, timeout=15)
    response.raise_for_status()
    payload = response.json()
    if "data" not in payload:
        raise ValueError(f"Alpha Vantage error for {function_name}: {payload}")
    cleaned = [
        {"date": item["date"], "value": float(item["value"])}
        for item in payload["data"]
        if item["value"] not in (".", None, "")
    ]
    cleaned.sort(key=lambda item: item["date"])
    return cleaned[-days:]


def get_commodity_history(commodity_name, days=90):
    """Returns cleaned [{date, value}, ...] price history for one commodity. Uses cache when fresh.

    Returns an empty list (rather than raising) if the underlying API call fails - e.g.
    Alpha Vantage's free tier 25-requests/day limit, shared across all commodities and
    all environments using this key. One exhausted commodity should degrade that one
    chart, not crash the entire page - callers already handle len(history) < 2.
    """
    cached = _read_cache(commodity_name)
    if cached is not None:
        return cached

    source_info = COMMODITY_SOURCE_MAP[commodity_name]
    try:
        if source_info["source"] == "fred":
            data = _fetch_fred(source_info["id"], days=days)
        else:
            data = _fetch_alpha(source_info["function"], days=days)
    except Exception:
        _write_cache(commodity_name, [], is_failure=True)
        return []

    _write_cache(commodity_name, data)
    return data


def get_commodity_prices(industry, days=90):
    """Returns {commodity_name: [{date, value}, ...]} for every commodity relevant to the industry."""
    if industry not in INDUSTRY_COMMODITIES:
        raise ValueError(f"Unknown industry: {industry}")

    return {
        commodity_name: get_commodity_history(commodity_name, days=days)
        for commodity_name in INDUSTRY_COMMODITIES[industry]
    }


if __name__ == "__main__":
    for industry in INDUSTRY_COMMODITIES:
        print(f"\n=== {industry} ===")
        data = get_commodity_prices(industry)
        for commodity, history in data.items():
            if history:
                first, last = history[0], history[-1]
                pct_change = (last["value"] - first["value"]) / first["value"] * 100
                print(f"  {commodity}: {len(history)} points | {first['date']}={first['value']} -> {last['date']}={last['value']} ({pct_change:+.1f}%)")
            else:
                print(f"  {commodity}: NO DATA")
