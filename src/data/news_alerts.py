import os
import json
from datetime import datetime, timedelta
import requests

from src.config import get_secret

NEWS_API_KEY = get_secret("NEWS_API_KEY")
NEWS_API_URL = "https://newsapi.org/v2/everything"
CACHE_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "cache")


def _cache_path(subject, days):
    safe_name = "".join(c if c.isalnum() else "_" for c in subject)
    return os.path.join(CACHE_DIR, f"news_{safe_name}_{days}d.json")


def _read_cache(subject, days, max_age_hours=24):
    path = _cache_path(subject, days)
    if not os.path.exists(path):
        return None
    with open(path) as f:
        cached = json.load(f)
    age_hours = (datetime.now() - datetime.fromisoformat(cached["timestamp"])).total_seconds() / 3600
    return cached["data"] if age_hours < max_age_hours else None


def _write_cache(subject, days, data):
    os.makedirs(CACHE_DIR, exist_ok=True)
    with open(_cache_path(subject, days), "w") as f:
        json.dump({"timestamp": datetime.now().isoformat(), "data": data}, f)

# Keywords that signal a supply-chain-relevant breaking event, not routine news.
RISK_KEYWORDS = [
    "tariff", "sanctions", "export ban", "strike", "conflict",
    "war", "instability", "disruption", "blockade",
]

REGULATORY_KEYWORDS = [
    "tariff", "trade war", "export control", "import ban", "trade agreement",
    "customs", "trade restriction", "trade deal", "WTO dispute",
]

SHIPPING_ROUTE_QUERIES = {
    "Red Sea / Suez Canal": '"Red Sea" OR "Suez Canal"',
    "Panama Canal": '"Panama Canal"',
    "US West Coast Ports": '"Port of Los Angeles" OR "Port of Long Beach" OR "West Coast ports"',
    "US East Coast Ports": '"Port of New York" OR "Port of Savannah" OR "East Coast ports" OR "ILA strike"',
    "Strait of Malacca": '"Strait of Malacca"',
}


def _risk_query(subject_expr, keywords):
    """Wraps an already-formed query expression with a risk keyword clause.

    `subject_expr` must already be a complete, correctly-quoted query fragment
    (e.g. '"China"' for a single phrase, or '("Red Sea" OR "Suez Canal")' for a
    multi-term route). This function only adds grouping parentheses - it must NOT
    add its own quotes, or a multi-term subject_expr would get nested inside an
    outer literal-string quote and stop matching as a boolean expression.

    Multi-word keywords (e.g. "export ban") must be quoted individually here, or
    NewsAPI parses them as separate words - which once caused bare "ban" to match
    unrelated headlines like cricket score recaps ("BAN vs AUS") and an unrelated
    social-media-ban news story.
    """
    quoted_keywords = [f'"{kw}"' if " " in kw else kw for kw in keywords]
    keyword_clause = " OR ".join(quoted_keywords)
    return f'({subject_expr}) AND ({keyword_clause})'


def get_news_risk_count(subject_expr, cache_key, keywords=RISK_KEYWORDS, days=7):
    """Counts recent news articles matching subject_expr alongside the given keywords.

    This is the 'fast alert layer' - it doesn't replace the slow-moving baseline
    (World Bank scores, hand-curated shipping status), it sits on top of it to catch
    sudden events between baseline updates. Cached for 24 hours since this signal is
    meant to be checked daily/weekly, not on every page load.

    `cache_key` must be unique per distinct keyword set used for the same subject -
    e.g. "China" with the default risk keywords and "China" with regulatory keywords
    need different cache_keys, or they'd collide and return each other's results.
    """
    cached = _read_cache(cache_key, days)
    if cached is not None:
        return cached

    from_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
    params = {
        # qInTitle (not q) restricts matching to the headline only. Searching full
        # article text caused massive false positives during unrelated global events
        # (e.g. World Cup coverage incidentally mentioning "crackdown" or "conflict"
        # somewhere in an article about Mexico/Brazil/Argentina). A headline that
        # pairs the subject with a risk keyword is a far stronger signal.
        "qInTitle": _risk_query(subject_expr, keywords),
        "language": "en",
        "from": from_date,
        "sortBy": "publishedAt",
        "pageSize": 10,
        "apiKey": NEWS_API_KEY,
    }
    response = requests.get(NEWS_API_URL, params=params, timeout=15)
    response.raise_for_status()
    data = response.json()
    if data.get("status") != "ok":
        raise ValueError(f"NewsAPI error: {data}")

    result = {
        "total_matches": data["totalResults"],
        "sample_headlines": [a["title"] for a in data["articles"][:5]],
    }
    _write_cache(cache_key, days, result)
    return result


def ratio_to_adjustment(ratio):
    """Converts a 'how much busier than usual' ratio into a 0-20 risk adjustment.

    This adjustment gets added on top of a slow baseline score (e.g. World Bank's
    annual political stability score) to reflect breaking events the baseline hasn't
    caught up to yet. Using a RATIO instead of a raw count matters: a naturally
    newsworthy country like China always has thousands of risk-keyword mentions,
    while a quiet country like Vietnam might have a handful. A raw count would peg
    China at max risk permanently and never flag a real spike for Vietnam. Comparing
    each subject to its OWN recent baseline lets a genuine spike stand out either way.
    """
    if ratio >= 2.5:
        return 20
    elif ratio >= 1.8:
        return 12
    elif ratio >= 1.3:
        return 6
    elif ratio >= 1.1:
        return 2
    return 0


MIN_RECENT_COUNT_FOR_ALERT = 3


def get_relative_alert(subject_expr, cache_key, keywords=RISK_KEYWORDS, recent_days=7, baseline_days=30):
    """Compares the last `recent_days` of risk-keyword mentions to the subject's own
    normal rate over the prior `baseline_days`, and returns a spike ratio + adjustment.

    Subjects with very few baseline mentions (quiet routes/countries) can swing from
    1 to 4 articles and produce a huge ratio that looks like a spike but is really just
    small-sample noise. MIN_RECENT_COUNT_FOR_ALERT requires a meaningful absolute volume
    of coverage before any adjustment is applied, regardless of how big the ratio looks.
    """
    recent = get_news_risk_count(subject_expr, cache_key, keywords, days=recent_days)
    last_30 = get_news_risk_count(subject_expr, cache_key, keywords, days=baseline_days)

    recent_count = recent["total_matches"]
    baseline_window_days = baseline_days - recent_days
    baseline_only_count = max(last_30["total_matches"] - recent_count, 0)
    baseline_weekly_rate = (
        (baseline_only_count / baseline_window_days) * recent_days
        if baseline_window_days > 0 else 0
    )

    ratio = recent_count / max(baseline_weekly_rate, 1)
    adjustment = ratio_to_adjustment(ratio) if recent_count >= MIN_RECENT_COUNT_FOR_ALERT else 0

    return {
        "recent_count": recent_count,
        "baseline_weekly_rate": round(baseline_weekly_rate, 1),
        "ratio": round(ratio, 2),
        "adjustment": adjustment,
        "sample_headlines": recent["sample_headlines"],
    }


def get_country_alert(country_name, recent_days=7, baseline_days=30):
    """country_name should be a full name like 'China' or 'Taiwan', not a country code."""
    subject_expr = f'"{country_name}"'
    return get_relative_alert(subject_expr, country_name, RISK_KEYWORDS, recent_days, baseline_days)


def get_route_alert(route_name, recent_days=7, baseline_days=30):
    if route_name not in SHIPPING_ROUTE_QUERIES:
        raise ValueError(f"Unknown route: {route_name}")
    subject_expr = f'({SHIPPING_ROUTE_QUERIES[route_name]})'
    return get_relative_alert(subject_expr, route_name, RISK_KEYWORDS, recent_days, baseline_days)


def get_industry_alert(industry, keywords, cache_suffix, recent_days=7, baseline_days=30):
    """Generic version of get_country_alert/get_route_alert for industry-level signals
    (regulatory/trade news, climate/disaster news) using a custom keyword set.
    `cache_suffix` keeps these cached separately from any other alert on the same industry name.
    """
    subject_expr = f'"{industry}"'
    cache_key = f"{industry}_{cache_suffix}"
    return get_relative_alert(subject_expr, cache_key, keywords, recent_days, baseline_days)


if __name__ == "__main__":
    print("=== Country Alerts (sample) ===")
    for country in ["China", "Taiwan", "Ukraine", "Vietnam"]:
        alert = get_country_alert(country)
        print(f"\n{country}: {alert['recent_count']} this week vs {alert['baseline_weekly_rate']}/week normal "
              f"(ratio {alert['ratio']}x) -> +{alert['adjustment']} risk adjustment")
        for h in alert["sample_headlines"][:3]:
            print(f"  - {h}")

    print("\n=== Shipping Route Alerts (sample) ===")
    for route in ["Red Sea / Suez Canal", "Panama Canal"]:
        alert = get_route_alert(route)
        print(f"\n{route}: {alert['recent_count']} this week vs {alert['baseline_weekly_rate']}/week normal "
              f"(ratio {alert['ratio']}x) -> +{alert['adjustment']} risk adjustment")
        for h in alert["sample_headlines"][:3]:
            print(f"  - {h}")
