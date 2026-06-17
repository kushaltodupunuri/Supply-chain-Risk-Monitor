import os
import json
from datetime import datetime, timedelta
import requests

from src.config import get_secret

FRED_API_KEY = get_secret("FRED_API_KEY")
CACHE_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "cache")

# FX series available via FRED's free H.10 release (vs USD). Countries not listed here
# don't have a free daily FRED series - currency_risk.py treats those as "no data" and
# excludes them rather than guessing. Notably missing: Taiwan, Vietnam, Bangladesh,
# Argentina, Ukraine (no free series), and Saudi Arabia/UAE (pegged currencies with no
# meaningful daily series) and Russia (sanctions-affected, no current free series).
FX_SERIES_MAP = {
    "CN": "DEXCHUS", "KR": "DEXKOUS", "MX": "DEXMXUS", "JP": "DEXJPUS",
    "DE": "DEXUSEU", "IE": "DEXUSEU", "IN": "DEXINUS", "BR": "DEXBZUS",
    "AU": "DEXUSAL", "SG": "DEXSIUS", "MY": "DEXMAUS",
    "CA": "DEXCAUS", "FR": "DEXUSEU", "GB": "DEXUSUK",
}


def _cache_path(series_id):
    return os.path.join(CACHE_DIR, f"fx_{series_id}.json")


def _read_cache(series_id, max_age_hours=24):
    path = _cache_path(series_id)
    if not os.path.exists(path):
        return None
    with open(path) as f:
        cached = json.load(f)
    age_hours = (datetime.now() - datetime.fromisoformat(cached["timestamp"])).total_seconds() / 3600
    return cached["data"] if age_hours < max_age_hours else None


def _write_cache(series_id, data):
    os.makedirs(CACHE_DIR, exist_ok=True)
    with open(_cache_path(series_id), "w") as f:
        json.dump({"timestamp": datetime.now().isoformat(), "data": data}, f)


def get_fx_history(country_code, days=90):
    """Returns [{date, value}, ...] daily exchange rate history (vs USD) for a
    country, or None if no free FRED series exists for that country's currency,
    or if the API call fails for any reason.
    """
    series_id = FX_SERIES_MAP.get(country_code)
    if series_id is None:
        return None

    cached = _read_cache(series_id)
    if cached is not None:
        return cached

    start_date = (datetime.now() - timedelta(days=days * 2)).strftime("%Y-%m-%d")
    url = "https://api.stlouisfed.org/fred/series/observations"
    params = {
        "series_id": series_id,
        "api_key": FRED_API_KEY,
        "file_type": "json",
        "observation_start": start_date,
    }
    try:
        response = requests.get(url, params=params, timeout=15)
        response.raise_for_status()
        observations = response.json()["observations"]
    except Exception:
        return None

    cleaned = [
        {"date": o["date"], "value": float(o["value"])}
        for o in observations
        if o["value"] != "."
    ]
    data = cleaned[-days:]
    _write_cache(series_id, data)
    return data


if __name__ == "__main__":
    for code in FX_SERIES_MAP:
        history = get_fx_history(code)
        if history:
            print(f"{code}: {len(history)} points, last={history[-1]}")
        else:
            print(f"{code}: NO DATA")
