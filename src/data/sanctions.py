import re
import requests

from src.config import get_secret

# Official US government Consolidated Screening List (OFAC SDN + several other
# restricted-party lists), via trade.gov's developer API. Free signup required:
# https://developer.trade.gov/apis - replaces the old direct SDN.CSV download,
# which is now served from a host with a broken certificate chain (works in
# browsers thanks to Windows' more lenient validation, fails standard Python/
# Linux TLS verification - which would also fail on Streamlit Cloud).
CSL_SEARCH_URL = "https://data.trade.gov/consolidated_screening_list/v1/search"
TRADE_GOV_API_KEY = get_secret("TRADE_GOV_API_KEY")

MIN_NAME_LENGTH = 4  # below this an exact-match check is still risky (e.g. very
# short legal names), so we skip rather than show a potentially wrong result.


def _normalize(name):
    return re.sub(r"\s+", " ", name.strip().upper())


def check_sanctions_status(entity_name):
    """Checks whether entity_name appears on the Consolidated Screening List.

    Requires an exact (case/whitespace-insensitive) name match. The underlying
    API's own "name" search is intentionally broad/fuzzy - a compliance tool is
    supposed to surface anything worth a human's attention - and an earlier,
    looser whole-word-substring check on our side incorrectly flagged "Apple" as
    a match against "ORIENTAL APPLE COMPANY PTE LTD". Exact match trades recall
    (it'll miss a listed entity that adds "Ltd"/"Group"/etc.) for not falsely
    flagging real companies, which matters more for a result shown as a fact.

    Returns {"checked": bool, "sanctioned": bool, "matched_name": str or None}.
    `checked` is False if no API key is configured or the entity name is too
    short to check reliably - callers should treat that as "unknown", not "clear".
    """
    entity_name = entity_name.strip()
    if not TRADE_GOV_API_KEY or len(entity_name) < MIN_NAME_LENGTH:
        return {"checked": False, "sanctioned": False, "matched_name": None}

    response = requests.get(
        CSL_SEARCH_URL,
        params={"name": entity_name, "size": 10},
        headers={"subscription-key": TRADE_GOV_API_KEY},
        timeout=15,
    )
    response.raise_for_status()
    results = response.json().get("results", [])

    needle = _normalize(entity_name)
    for item in results:
        listed_name = str(item.get("name", ""))
        if _normalize(listed_name) == needle:
            return {"checked": True, "sanctioned": True, "matched_name": listed_name}

    return {"checked": True, "sanctioned": False, "matched_name": None}


def check_sanctions_status_safe(entity_name):
    try:
        return check_sanctions_status(entity_name)
    except Exception:
        return {"checked": False, "sanctioned": False, "matched_name": None}
