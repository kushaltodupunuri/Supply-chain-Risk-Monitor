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
