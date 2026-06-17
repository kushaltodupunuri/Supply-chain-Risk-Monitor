import json
import ollama
from groq import Groq

from src.config import get_secret

OLLAMA_MODEL = "llama3.2"
GROQ_MODEL = "llama-3.1-8b-instant"
GROQ_API_KEY = get_secret("GROQ_API_KEY")


def _call_llm(prompt):
    """Uses Groq (free-tier cloud API) when a key is configured - this is what runs
    once deployed to Streamlit Cloud. Falls back to local Ollama otherwise, which is
    what runs during local development with no API key needed at all.
    """
    if GROQ_API_KEY:
        client = Groq(api_key=GROQ_API_KEY)
        response = client.chat.completions.create(
            model=GROQ_MODEL,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=250,
        )
        return response.choices[0].message.content.strip()

    response = ollama.chat(model=OLLAMA_MODEL, messages=[{"role": "user", "content": prompt}])
    return response["message"]["content"].strip()


def generate_risk_summary(industry, result, commodity_changes, company_name=None):
    """Generates a 3-4 sentence plain English risk brief.

    industry: str
    result: the dict returned by risk_engine.calculate_risk_score(industry)
    commodity_changes: {commodity_name: pct_change_float}, e.g. {"Copper": 12.3, "Steel": -2.1}
    """
    commodity_lines = [
        f"- {name}: {'up' if pct >= 0 else 'down'} {abs(pct):.1f}% over the shown period"
        for name, pct in commodity_changes.items()
    ]
    commodity_text = "\n".join(commodity_lines) if commodity_lines else "No commodity data available."

    sub_scores = result["sub_scores"]
    labeled_scores = {
        "Supplier Concentration": sub_scores["supplier"],
        "Commodity Prices": sub_scores["commodity"],
        "Logistics & Shipping": sub_scores["logistics"],
        "Geopolitical Factors": sub_scores["geopolitical"],
    }
    biggest_risk = max(labeled_scores, key=labeled_scores.get)

    company_context = ""
    if company_name:
        company_context = (
            f"The analysis is for {company_name}. Frame the summary around their "
            f"known position in the {industry} supply chain."
        )

    prompt = f"""You are a senior supply chain risk analyst writing a brief for a supply chain executive.

Industry: {industry}
{company_context}

Current risk scores (0-100, higher = more risk):
- Overall Risk: {result['total']}/100
- Supplier Concentration Risk: {sub_scores['supplier']}/100
- Commodity Price Risk: {sub_scores['commodity']}/100
- Logistics & Shipping Risk: {sub_scores['logistics']}/100
- Geopolitical Risk: {sub_scores['geopolitical']}/100

Key commodity price movements:
{commodity_text}

The highest-risk dimension is: {biggest_risk}

Write a 3-4 sentence plain English summary of the current supply chain risk situation. Rules:
- Do NOT mention the numerical scores directly (no "78/100" in the text)
- Start with the single biggest risk and name it specifically (don't be vague)
- Mention at least one specific commodity or country by name
- End with one forward-looking statement about what to watch
- Write as if briefing a busy VP of Supply Chain - direct, no filler words
- Output ONLY the summary itself - no preamble like "Here is a summary"
"""

    return _call_llm(prompt)


def generate_risk_summary_safe(industry, result, commodity_changes, company_name=None):
    """Same as generate_risk_summary, but never raises - falls back to a templated
    summary if the LLM call fails, so a missing key or local server hiccup never breaks the UI.
    """
    try:
        return generate_risk_summary(industry, result, commodity_changes, company_name)
    except ollama.ResponseError:
        return (
            f"AI summary unavailable - model '{OLLAMA_MODEL}' not found locally. "
            f"Run `ollama pull {OLLAMA_MODEL}` and try again. "
            f"Overall risk score: {result['total']}/100."
        )
    except Exception as e:
        hint = (
            "check your GROQ_API_KEY"
            if GROQ_API_KEY
            else "is Ollama running? Install from ollama.com, it should start automatically"
        )
        return (
            f"AI summary unavailable ({hint}). "
            f"Overall risk score: {result['total']}/100."
        )


SUPPORTED_INDUSTRIES = ["Electronics", "Automotive", "Pharma", "Retail", "Food & Beverage"]


def detect_company_industry(company_name):
    """Identifies which of the 5 supported industries a company actually belongs to,
    so the user doesn't have to also manually pick the matching industry dropdown
    value (which is error-prone - e.g. picking "Automotive" while typing "Apple").

    Returns one of SUPPORTED_INDUSTRIES, or None if the model isn't confident it
    recognizes the company - same honesty calibration as the other company functions,
    so an obscure or made-up name doesn't get force-matched to a random industry.
    """
    options_text = ", ".join(SUPPORTED_INDUSTRIES)
    prompt = f"""Which ONE of these industries does the company "{company_name}" primarily belong to?

Options: {options_text}

Only answer with a specific industry if you are highly confident "{company_name}" is a
real, specific company you recognize. If you don't recognize it, or it doesn't clearly
fit one of these industries, respond with exactly: UNKNOWN

Respond with ONLY one of these exact words and nothing else: {options_text}, UNKNOWN
"""
    raw = _call_llm(prompt).strip().lower()
    if "food" in raw or "beverage" in raw:
        return "Food & Beverage"
    for industry in SUPPORTED_INDUSTRIES:
        if industry.lower() in raw:
            return industry
    return None


def detect_company_industry_safe(company_name):
    try:
        return detect_company_industry(company_name)
    except Exception:
        return None


def generate_company_sourcing_countries(company_name, industry):
    """Lists the countries a specific, recognized company is publicly known to source
    from or manufacture in - this is often a longer, more complete list than the 4-5
    generic countries used for the industry-wide baseline (e.g. Apple's real supply
    chain spans far more countries than just "Electronics in general").

    Returns an empty list if the model doesn't have specific, real knowledge of this
    company's sourcing - same honesty calibration as the other company functions. The
    caller should fall back to the generic industry-level breakdown in that case.
    """
    prompt = f"""You are a supply chain analyst evaluating "{company_name}" in the {industry} industry.

First, decide: is "{company_name}" a real, specific company you can name verified, well-known
facts about (e.g. its actual named factories, suppliers, or sourcing countries)? Many company
names you are given will be small, obscure, or entirely made up. Generic-sounding or
unfamiliar names should be treated as NOT known - do not guess or extrapolate countries just
because they sound typical for the {industry} industry, and do not invent a plausible-looking
list just because the name sounds like a real company.

If, and only if, "{company_name}" is a real company you have specific knowledge of, list the
countries it is publicly known to source components from or manufacture in. List as many real,
known countries as you're confident about - do not artificially limit to a small number if you
know of more.

For each country, give:
- country: the full country name in English
- country_code: the ISO 3166-1 alpha-2 code (e.g. "US", "CN", "TW")
- product: what is sourced or manufactured there (short phrase)
- share: your best estimate of relative sourcing share, as a rough percentage (all entries should sum to roughly 100)

Respond with ONLY a JSON array, nothing else, in this exact format:
[{{"country": "...", "country_code": "...", "product": "...", "share": number}}, ...]

If "{company_name}" is not known with high confidence, respond with exactly: []
When in doubt, respond with: []
"""
    raw = _call_llm(prompt)
    start, end = raw.index("["), raw.rindex("]") + 1
    data = json.loads(raw[start:end])
    return [
        {
            "country": str(item.get("country", "")),
            "country_code": str(item.get("country_code", "")).upper(),
            "product": str(item.get("product", "")),
            "share": float(item.get("share", 0)),
        }
        for item in data
        if item.get("country") and item.get("country_code")
    ]


def generate_company_sourcing_countries_safe(company_name, industry):
    try:
        return generate_company_sourcing_countries(company_name, industry)
    except Exception:
        return []


def generate_company_context(company_name, industry):
    """Generates a brief, clearly-caveated qualitative note about a specific company's
    known supply chain characteristics.

    This intentionally does NOT change the quantitative risk scores. There is no free,
    reliable data source that publishes verified supplier-country breakdowns per company,
    so inventing specific numbers here would look precise while being fabricated. Instead,
    the model is explicitly instructed to say when it doesn't have reliable knowledge of
    a company, rather than guessing - this note is illustrative context, not a scored input.
    """
    prompt = f"""You are a supply chain analyst. Based on generally known public information,
write a brief note about {company_name}'s known supply chain characteristics relevant to
the {industry} industry - e.g. notable suppliers, manufacturing locations, or sourcing
concentration, if these are part of well-established public knowledge.

Rules:
- If {company_name} is not a well-known company, or you don't have reliable public
  knowledge of their supply chain, say so plainly instead of guessing or inventing details.
- Do not state specific percentages or statistics unless they are widely reported public facts.
- Keep it to 2-3 sentences, direct, no filler.
- Output ONLY the note itself - no preamble.
"""
    return _call_llm(prompt)


def generate_company_context_safe(company_name, industry):
    try:
        return generate_company_context(company_name, industry)
    except Exception:
        return f"Company-specific context for {company_name} is currently unavailable."


def generate_company_score_adjustment(company_name, industry):
    """Estimates how a specific company's risk profile likely differs from the
    industry-average baseline, using only the model's general public knowledge.

    Returns adjustments in the range -15 to +15 for each of the 4 sub-scores, plus
    `known` (whether the model claims reliable knowledge of this company) and a short
    `reasoning` string. When `known` is False, the caller should treat all adjustments
    as 0 - this is what keeps the system honest for obscure or made-up company names
    instead of letting the model invent a plausible-looking number from nothing.
    """
    prompt = f"""You are a supply chain risk analyst evaluating "{company_name}" in the {industry} industry.

First, decide: is "{company_name}" a real, specific company you can name verified, well-known
facts about (e.g. its actual named suppliers, factories, or sourcing countries)? Many company
names you are given will be small, obscure, or entirely made up. Generic-sounding or
unfamiliar names should be treated as NOT known - do not guess or extrapolate from the name
itself, and do not invent plausible-sounding details just because a name sounds like a real
company. Only mark a company as known if you could list specific, real facts about it.

If known, estimate how its supply chain risk likely differs from the {industry} industry
average, using only real facts. For each dimension return an adjustment from -15 (notably
lower risk than the industry average) to +15 (notably higher risk):
- supplier: supplier/sourcing concentration risk
- commodity: commodity price exposure risk
- logistics: shipping/logistics risk
- geopolitical: geopolitical exposure risk

Respond with ONLY a JSON object, nothing else, in this exact format:
{{"known": true or false, "supplier": number, "commodity": number, "logistics": number, "geopolitical": number, "reasoning": "one short sentence naming a specific real fact, or empty if not known"}}

If "{company_name}" is not known with high confidence, set "known" to false and all four
numeric adjustments to exactly 0. When in doubt, set "known" to false.
"""
    raw = _call_llm(prompt)
    try:
        start, end = raw.index("{"), raw.rindex("}") + 1
        data = json.loads(raw[start:end])
        return {
            "known": bool(data.get("known", False)),
            "supplier": max(-15, min(15, float(data.get("supplier", 0)))),
            "commodity": max(-15, min(15, float(data.get("commodity", 0)))),
            "logistics": max(-15, min(15, float(data.get("logistics", 0)))),
            "geopolitical": max(-15, min(15, float(data.get("geopolitical", 0)))),
            "reasoning": str(data.get("reasoning", "")),
        }
    except Exception:
        return {"known": False, "supplier": 0, "commodity": 0, "logistics": 0, "geopolitical": 0, "reasoning": ""}


RECOMMENDATION_LIBRARY = {
    "supplier": {
        "title": "Qualify backup suppliers in alternative regions",
        "detail_template": (
            "Given supplier concentration risk in {industry}, identify and qualify 1-2 "
            "backup suppliers in {alternative_region}. Aim to shift 15-20% of volume within 6 months."
        ),
        "priority": "High",
    },
    "commodity": {
        "title": "Evaluate commodity hedging or longer-term contracts",
        "detail_template": (
            "With {commodity} showing price risk, explore 6-12 month forward contracts "
            "with key material suppliers to lock in current rates before further increases."
        ),
        "priority": "High",
    },
    "logistics": {
        "title": "Evaluate air freight for time-critical components",
        "detail_template": (
            "Current ocean shipping conditions may add delays to transit times. For "
            "components with lead times under 30 days, evaluate whether air freight premium is justified."
        ),
        "priority": "Medium",
    },
    "geopolitical": {
        "title": "Map tariff exposure and assess nearshoring opportunities",
        "detail_template": (
            "Conduct a tariff exposure analysis across your {industry} supply base. "
            "Evaluate {alternative_region} as nearshoring options for top sourced categories."
        ),
        "priority": "Medium",
    },
}

ALTERNATIVE_REGIONS = {
    "Electronics": "Vietnam and India",
    "Pharma": "India and Ireland",
    "Automotive": "Mexico and Eastern Europe",
    "Retail": "Vietnam, Bangladesh, and India",
    "Food & Beverage": "Brazil and Australia",
}

PRIMARY_COMMODITIES = {
    "Electronics": "copper and semiconductor-related materials",
    "Pharma": "active pharmaceutical ingredients",
    "Automotive": "steel and aluminum",
    "Retail": "cotton and shipping fuel",
    "Food & Beverage": "wheat and corn",
}


def generate_recommendations(industry, result):
    """Returns the top 3 recommendations, ranked by which sub-score is currently
    highest. Uses a fixed top-3 rather than a >60 threshold, since real computed
    scores mostly sit in the moderate 25-55 range (see docs/03-RISK-SCORING.md) -
    a high threshold would return nothing most of the time.
    """
    sorted_areas = sorted(result["sub_scores"].items(), key=lambda x: x[1], reverse=True)
    top_areas = [area for area, _ in sorted_areas[:3]]

    recommendations = []
    for area in top_areas:
        template = RECOMMENDATION_LIBRARY[area]
        detail = template["detail_template"].format(
            industry=industry,
            alternative_region=ALTERNATIVE_REGIONS.get(industry, "Southeast Asia"),
            commodity=PRIMARY_COMMODITIES.get(industry, "key commodities"),
        )
        recommendations.append({"title": template["title"], "detail": detail, "priority": template["priority"]})

    return recommendations
