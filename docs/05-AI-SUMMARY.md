# AI Summary & Recommendations — How It Works

This explains the AI layer: what it does, why it's there, how to implement it, and how to prompt it correctly so it produces useful output.

---

## What the AI Actually Does

The AI does not calculate risk. Your Python model does that. The AI's job is:

1. **Translate numbers into language.** A recruiter or executive doesn't know what a "78 geopolitical risk score" means. The AI says "The electronics industry faces significant geopolitical risk due to heavy semiconductor dependence on Taiwan at a time of elevated cross-strait tensions." That's actionable.

2. **Generate recommendations.** Based on the risk profile, the AI suggests 3 specific actions. These are grounded in actual supply chain strategy — not made up.

3. **Personalize the output.** If a company name is entered, the AI can frame the summary around that company's known supply chain characteristics.

---

## Why Claude (Not ChatGPT/OpenAI)

For this use case, Claude is better for these reasons:

- **Follows formatting instructions better.** You need exactly 3-4 sentences. Claude reliably stays in that range. OpenAI's GPT models tend to be wordier.
- **More conservative.** Claude doesn't hallucinate specific statistics unless given them. This matters because you're passing real data and don't want the AI inventing fake numbers to sound smart.
- **Anthropic API is straightforward.** `pip install anthropic` and you're done.

---

## Setting Up the Anthropic Client

```python
# At the top of your AI module: src/ai/summary.py

import anthropic
import os
from dotenv import load_dotenv

load_dotenv()

client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
```

**Which model to use:**

- `claude-haiku-4-5-20251001` — Fast and very cheap. Good for short summaries. Use this.
- `claude-sonnet-4-6` — Smarter, more expensive. Use only if Haiku's output quality isn't good enough.

For 3-4 sentence summaries, Haiku is more than sufficient and costs roughly 100x less per call.

---

## The Risk Summary Function

```python
def generate_risk_summary(industry, scores, commodity_changes, company_name=None):
    """
    Generates a 3-4 sentence plain English risk brief.
    
    scores: dict with keys total, supplier, commodity, logistics, geopolitical (all 0-100)
    commodity_changes: dict with commodity name → % change over 90 days
        e.g. {"Copper": +12.3, "Steel": -2.1, "Oil": +8.7}
    """
    
    # Format commodity data for the prompt
    commodity_lines = []
    for commodity, pct_change in commodity_changes.items():
        direction = "up" if pct_change > 0 else "down"
        commodity_lines.append(f"- {commodity}: {direction} {abs(pct_change):.1f}% over 90 days")
    commodity_text = "\n".join(commodity_lines)
    
    # Determine the highest-risk dimension
    sub_scores = {
        "Supplier Concentration": scores["supplier"],
        "Commodity Prices": scores["commodity"],
        "Logistics & Shipping": scores["logistics"],
        "Geopolitical Factors": scores["geopolitical"]
    }
    biggest_risk = max(sub_scores, key=sub_scores.get)
    
    # Build the company context if provided
    company_context = ""
    if company_name:
        company_context = f"The analysis is for {company_name}. Frame the summary around their known position in the {industry} supply chain."
    
    prompt = f"""You are a senior supply chain risk analyst writing a brief for a supply chain executive.

Industry: {industry}
{company_context}

Current Risk Scores (0-100, higher = more risk):
- Overall Risk: {scores['total']}/100
- Supplier Concentration Risk: {scores['supplier']}/100
- Commodity Price Risk: {scores['commodity']}/100
- Logistics & Shipping Risk: {scores['logistics']}/100
- Geopolitical Risk: {scores['geopolitical']}/100

Key commodity price movements (last 90 days):
{commodity_text}

The highest-risk dimension is: {biggest_risk}

Write a 3-4 sentence plain English summary of the current supply chain risk situation. Rules:
- Do NOT mention the numerical scores directly (no "78/100" in the text)
- Start with the single biggest risk and name it specifically (don't be vague)
- Mention at least one specific commodity or country by name
- End with one forward-looking statement about what to watch
- Write as if briefing a busy VP of Supply Chain — direct, no filler words
"""
    
    message = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=250,
        messages=[{"role": "user", "content": prompt}]
    )
    
    return message.content[0].text.strip()
```

**Example output for Electronics with high geopolitical risk:**
> "The electronics industry's most acute near-term risk stems from its semiconductor supply chain, where over 60% of advanced chip production remains concentrated in Taiwan amid ongoing geopolitical uncertainty in the strait. Copper prices have risen 12% over the past 90 days, adding cost pressure across circuit board and wiring component suppliers. Shipping costs remain elevated on trans-Pacific routes following continued Suez Canal rerouting, adding 2-3 weeks to Asia-Europe component deliveries. Watch for any escalation in US-China technology export controls, which could trigger secondary supplier restrictions."

---

## The Recommendations Function

Recommendations are AI-generated but guided by a template. You tell the AI which risk dimensions are elevated and it selects and writes appropriate recommendations.

```python
RECOMMENDATION_LIBRARY = {
    "supplier_high": [
        {
            "title": "Qualify backup suppliers in alternative regions",
            "detail_template": "Given high supplier concentration risk in {industry}, identify and qualify 1-2 backup suppliers in {alternative_region}. Aim to shift 15-20% of volume within 6 months.",
            "priority": "High"
        },
        {
            "title": "Conduct supplier financial health review",
            "detail_template": "Request current financial statements from top 5 suppliers. Identify any that are single-source for critical components.",
            "priority": "Medium"
        }
    ],
    "commodity_high": [
        {
            "title": "Evaluate commodity hedging or longer-term contracts",
            "detail_template": "With {commodity} prices up significantly, explore 6-12 month forward contracts with key material suppliers to lock in current rates before further increases.",
            "priority": "High"
        },
        {
            "title": "Accelerate material substitution review",
            "detail_template": "Review product designs for opportunities to substitute high-risk commodities with more stable alternatives where technically feasible.",
            "priority": "Medium"
        }
    ],
    "logistics_high": [
        {
            "title": "Evaluate air freight for time-critical components",
            "detail_template": "Current ocean shipping disruptions are adding 10-14 days to transit times. For components with lead times under 30 days, evaluate whether air freight premium is justified.",
            "priority": "High"
        },
        {
            "title": "Build safety stock on highest-risk SKUs",
            "detail_template": "Increase inventory buffer on top 20 components most exposed to shipping disruption. Target 45-60 days of stock vs. current levels.",
            "priority": "Medium"
        }
    ],
    "geopolitical_high": [
        {
            "title": "Map tariff exposure and assess nearshoring opportunities",
            "detail_template": "Conduct a full tariff exposure analysis across your {industry} supply base. Evaluate Mexico and Vietnam as nearshoring options for top 10 sourced categories.",
            "priority": "High"
        },
        {
            "title": "Monitor export control developments",
            "detail_template": "Assign someone to track US Commerce Department and BIS export control updates weekly. Brief leadership monthly on any changes affecting your supply base.",
            "priority": "Medium"
        }
    ]
}

def generate_recommendations(industry, scores):
    # Determine which risk areas are high
    high_risk_areas = []
    if scores["supplier"] > 60:
        high_risk_areas.append("supplier_high")
    if scores["commodity"] > 60:
        high_risk_areas.append("commodity_high")
    if scores["logistics"] > 60:
        high_risk_areas.append("logistics_high")
    if scores["geopolitical"] > 60:
        high_risk_areas.append("geopolitical_high")
    
    # If nothing is high risk, use the top 2 scores
    if not high_risk_areas:
        sorted_scores = sorted([
            ("supplier_high", scores["supplier"]),
            ("commodity_high", scores["commodity"]),
            ("logistics_high", scores["logistics"]),
            ("geopolitical_high", scores["geopolitical"])
        ], key=lambda x: x[1], reverse=True)
        high_risk_areas = [sorted_scores[0][0], sorted_scores[1][0]]
    
    # Pick one recommendation per high-risk area (the first one), max 3 total
    recommendations = []
    for area in high_risk_areas[:3]:
        rec_template = RECOMMENDATION_LIBRARY[area][0]
        
        # Fill in template variables
        alternative_regions = {
            "Electronics": "Vietnam and India",
            "Pharma": "India and Ireland",
            "Automotive": "Mexico and Eastern Europe",
            "Retail": "Vietnam, Bangladesh, and India",
            "Food & Beverage": "Brazil and Australia"
        }
        
        commodities = {
            "Electronics": "copper and rare earth metals",
            "Pharma": "active pharmaceutical ingredients",
            "Automotive": "steel and aluminum",
            "Retail": "cotton and shipping fuel",
            "Food & Beverage": "wheat and corn"
        }
        
        detail = rec_template["detail_template"].format(
            industry=industry,
            alternative_region=alternative_regions.get(industry, "Southeast Asia"),
            commodity=commodities.get(industry, "key commodities")
        )
        
        recommendations.append({
            "title": rec_template["title"],
            "detail": detail,
            "priority": rec_template["priority"]
        })
    
    return recommendations
```

---

## Error Handling for the AI Call

API calls can fail. Handle this gracefully so the rest of the app still works:

```python
def generate_risk_summary_safe(industry, scores, commodity_changes, company_name=None):
    try:
        return generate_risk_summary(industry, scores, commodity_changes, company_name)
    except anthropic.APIConnectionError:
        return f"The {industry} industry is currently showing {'elevated' if scores['total'] > 60 else 'moderate'} supply chain risk. AI summary unavailable — please check your API connection."
    except anthropic.RateLimitError:
        return f"AI summary temporarily unavailable due to rate limits. Overall risk score: {scores['total']}/100."
    except Exception as e:
        return f"Risk analysis complete. Overall score: {scores['total']}/100. AI summary generation failed: please retry."
```

---

## Cost Management

With Claude Haiku at ~$0.25 per million input tokens and ~$1.25 per million output tokens, a typical call (400 input tokens, 100 output tokens) costs about **$0.0002** (less than a fraction of a cent).

For development: your $5 free credit will last for approximately **25,000 summary generations**. You will never come close to exhausting this in development.

For production (after deployment): add Streamlit's `@st.cache_data` decorator to cache AI summaries for the same industry+score combination. If the same inputs generate the same output, serve the cached version.

```python
@st.cache_data(ttl=3600)  # Cache for 1 hour
def generate_risk_summary_cached(industry, scores_tuple, commodity_data_str):
    # Convert back from tuple/str for the actual call
    scores = dict(scores_tuple)
    return generate_risk_summary_safe(industry, scores, ...)
```

---

## What Makes the AI Output Good vs. Generic

**Bad prompt (produces generic output):**
> "Summarize supply chain risks for Electronics."

**Good prompt (produces specific, useful output):**
> "Geopolitical risk is 85/100 primarily due to Taiwan semiconductor concentration. Copper is up 12% in 90 days. Write 3-4 sentences. Start with the single biggest risk. Mention Taiwan and copper specifically. End with what to watch."

The difference is that the good prompt gives the AI real data and specific constraints. The AI is not asked to know things — it's asked to translate the data you've already computed into language.

This is the professional way to use AI in enterprise software: **the AI translates; the model computes.**

Next: [docs/06-DEPLOYMENT.md](06-DEPLOYMENT.md) — How to put the app live on the internet for free.
