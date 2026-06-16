import os
import json
from datetime import datetime
import requests

WORLD_BANK_BASE_URL = "https://api.worldbank.org/v2/country"
CACHE_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "cache")


def _cache_path(country_code, indicator):
    safe_indicator = indicator.replace(".", "_")
    return os.path.join(CACHE_DIR, f"wb_{country_code}_{safe_indicator}.json")


def _read_cache(country_code, indicator, max_age_hours=168):
    """Default cache window is 7 days - World Bank data updates annually, so this
    just avoids re-fetching on every run during a single week of development/use.
    """
    path = _cache_path(country_code, indicator)
    if not os.path.exists(path):
        return None
    with open(path) as f:
        cached = json.load(f)
    age_hours = (datetime.now() - datetime.fromisoformat(cached["timestamp"])).total_seconds() / 3600
    return cached["data"] if age_hours < max_age_hours else None


def _write_cache(country_code, indicator, data):
    os.makedirs(CACHE_DIR, exist_ok=True)
    with open(_cache_path(country_code, indicator), "w") as f:
        json.dump({"timestamp": datetime.now().isoformat(), "data": data}, f)

COUNTRY_NAMES = {
    "CN": "China", "TW": "Taiwan", "KR": "South Korea",
    "VN": "Vietnam", "MY": "Malaysia", "IN": "India",
    "MX": "Mexico", "JP": "Japan", "DE": "Germany",
    "BD": "Bangladesh", "US": "United States", "BR": "Brazil",
    "AR": "Argentina", "AU": "Australia", "UA": "Ukraine",
    "IE": "Ireland", "SG": "Singapore",
}

# Countries each industry sources from. Used by the Week 2 risk model
# and the Week 3 map, but kept here since it's "where does data come from" info.
INDUSTRY_SOURCING_COUNTRIES = {
    "Electronics": ["TW", "CN", "KR", "VN", "MY"],
    "Pharma": ["CN", "IN", "IE", "SG"],
    "Automotive": ["CN", "MX", "JP", "DE", "KR"],
    "Retail": ["CN", "BD", "VN", "IN"],
    "Food & Beverage": ["US", "BR", "AR", "AU", "UA"],
}


def get_country_risk(country_code, indicator="GOV_WGI_PV.EST"):
    """Fetches the most recent non-null World Bank governance indicator value.

    GOV_WGI_PV.EST = Political Stability and Absence of Violence (-2.5 worst to +2.5 best)
    World Bank often has a 1-2 year reporting lag, so we look back up to 5 years
    and return the most recent year that actually has a value. Cached for 7 days.
    """
    cached = _read_cache(country_code, indicator)
    if cached is not None:
        return cached

    url = f"{WORLD_BANK_BASE_URL}/{country_code}/indicator/{indicator}"
    params = {"format": "json", "mrv": 5}
    response = requests.get(url, params=params, timeout=15)
    response.raise_for_status()
    payload = response.json()

    if len(payload) < 2 or payload[1] is None:
        raise ValueError(f"No data returned for {country_code}/{indicator}: {payload}")

    for entry in payload[1]:
        if entry["value"] is not None:
            result = {"value": entry["value"], "year": entry["date"]}
            _write_cache(country_code, indicator, result)
            return result

    raise ValueError(f"No non-null data found for {country_code}/{indicator} in the last 5 years")


def get_country_risk_batch(country_codes, indicator="GOV_WGI_PV.EST"):
    """Fetches country risk for a list of countries. Returns {country_code: {value, year}}."""
    results = {}
    for code in country_codes:
        try:
            results[code] = get_country_risk(code, indicator)
        except ValueError as e:
            results[code] = {"value": None, "year": None, "error": str(e)}
    return results


def get_country_risk_for_industry(industry, indicator="GOV_WGI_PV.EST"):
    """Convenience function: fetches risk for every country a given industry sources from."""
    if industry not in INDUSTRY_SOURCING_COUNTRIES:
        raise ValueError(f"Unknown industry: {industry}")
    countries = INDUSTRY_SOURCING_COUNTRIES[industry]
    return get_country_risk_batch(countries, indicator)


if __name__ == "__main__":
    for industry, countries in INDUSTRY_SOURCING_COUNTRIES.items():
        print(f"\n=== {industry} ===")
        risk_data = get_country_risk_for_industry(industry)
        for code, data in risk_data.items():
            name = COUNTRY_NAMES.get(code, code)
            if data["value"] is not None:
                print(f"  {name} ({code}): {data['value']:.2f} (year {data['year']})")
            else:
                print(f"  {name} ({code}): NO DATA - {data.get('error')}")
