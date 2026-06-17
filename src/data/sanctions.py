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

MIN_NAME_LENGTH = 4  # below this, matching against short acronyms like "BP", "GE",
# "HP" risks a false-positive hit against an unrelated longer listed name that
# happens to contain that token - safer to skip the check than show a wrong result.


def check_sanctions_status(entity_name):
    """Checks whether entity_name appears on the Consolidated Screening List.

    The underlying API is intentionally over-inclusive (a compliance screening
    tool is supposed to surface anything worth a human's attention), so a result
    is only counted as a match if the listed name also contains entity_name as a
    whole word - this is still a real, verifiable signal, but the absence of a
    match means "no listed-name match found", not a certified clean bill of health.

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

    pattern = re.compile(r"\b" + re.escape(entity_name.upper()) + r"\b")
    for item in results:
        listed_name = str(item.get("name", ""))
        if pattern.search(listed_name.upper()):
            return {"checked": True, "sanctioned": True, "matched_name": listed_name}

    return {"checked": True, "sanctioned": False, "matched_name": None}


def check_sanctions_status_safe(entity_name):
    try:
        return check_sanctions_status(entity_name)
    except Exception:
        return {"checked": False, "sanctioned": False, "matched_name": None}
