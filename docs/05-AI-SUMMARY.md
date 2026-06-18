# Summary & Recommendations — How It Works

*(This tab is labeled "Summary & Recommendations" in the app's UI - the content is still AI-generated under the hood, the word "AI" was just dropped from the displayed tab name.)*

**This doc was rewritten to match the live app.** The original plan used Anthropic's Claude API. The live app uses **Groq (deployed) / Ollama (local)** instead — both free, so the project has no paid dependency anywhere in the stack. Everything below matches `src/ai/summary.py`.

This explains the AI layer: what it does, why it's there, how it's implemented, and how it's prompted so it produces useful — and trustworthy — output.

---

## What the AI Actually Does

The AI does not calculate risk. The Python model in `src/models/` does that. The AI's job is:

1. **Translate numbers into language.** A recruiter or executive doesn't know what a "78 supplier concentration score" means. The AI says "the electronics industry's reliance on Taiwan-based semiconductor manufacturing is the dominant risk right now." That's actionable.
2. **Generate recommendations.** Based on which 3 categories currently score highest, the AI fills in a templated recommendation with industry-specific specifics.
3. **Personalize the output** for a named company — but only when it has real, specific knowledge of that company (see "The Honesty Calibration" below).

---

## Why Groq + Ollama (Not a Paid API)

```python
# src/ai/summary.py
OLLAMA_MODEL = "llama3.2"
GROQ_MODEL = "llama-3.1-8b-instant"
GROQ_API_KEY = get_secret("GROQ_API_KEY")

def _call_llm(prompt, temperature=None):
    if GROQ_API_KEY:
        client = Groq(api_key=GROQ_API_KEY)
        kwargs = {"temperature": temperature} if temperature is not None else {}
        response = client.chat.completions.create(
            model=GROQ_MODEL, messages=[{"role": "user", "content": prompt}],
            max_tokens=250, seed=42, **kwargs,
        )
        return response.choices[0].message.content.strip()

    options = {"temperature": temperature} if temperature is not None else {}
    options["seed"] = 42
    response = ollama.chat(model=OLLAMA_MODEL, messages=[{"role": "user", "content": prompt}], options=options)
    return response["message"]["content"].strip()
```

**Groq** (console.groq.com, free account, no credit card) is what runs once deployed to Streamlit Cloud, when `GROQ_API_KEY` is set. **Ollama** (ollama.com, install locally, `ollama pull llama3.2`) is what runs during local development with zero API key needed — Streamlit Cloud can't run Ollama itself (it needs a local model server), so the two providers split cleanly by environment. Every call to either provider goes through this one `_call_llm()` function, so the rest of the codebase doesn't need to know which provider is active.

---

## The Determinism Fix (A Real Bug, Not Just "AI Being Creative")

Every LLM call defaults to non-zero temperature — useful for natural-sounding prose, but a real problem for anything that's supposed to be a **stable fact**. The company-specific score adjustment, industry detection, and sourcing percentages all feed directly into the displayed risk score. Without a fixed temperature and seed, **the same company could show a different score on a different device, a different session, or after the cache expired** — which looked like (and was reported as) a bug, because it was one.

The fix: `temperature=0` and a fixed `seed=42` for every call that produces a number or classification:

```python
raw = _call_llm(prompt, temperature=0)  # detect_company_industry, generate_company_score_adjustment,
                                          # generate_company_sourcing_countries, generate_known_suppliers
```

Prose-only calls (the risk brief, recommendation detail text) keep the default temperature, since wording variety there doesn't undermine trust in a number the way an actually-different score would.

---

## The Risk Summary Function

```python
def generate_risk_summary(industry, result, commodity_changes, company_name=None):
    """3-4 sentence plain English risk brief.

    result: the dict from risk_engine.calculate_risk_score(industry) - has total,
        label, sub_scores (5 categories), weights, details.
    commodity_changes: {commodity_name: pct_change_float}, e.g. {"Copper": 121.9, "Oil (WTI)": 34.6}
    """
    sub_scores = result["sub_scores"]
    labeled_scores = {
        "Supplier Concentration": sub_scores["supplier"],
        "Commodity Prices": sub_scores["commodity"],
        "Logistics & Shipping": sub_scores["logistics"],
        "Geopolitical Factors": sub_scores["geopolitical"],
        "Regulatory & Trade Policy": sub_scores["regulatory"],
    }
    biggest_risk = max(labeled_scores, key=labeled_scores.get)

    company_context = (
        f"The analysis is for {company_name}. Frame the summary around their "
        f"known position in the {industry} supply chain."
    ) if company_name else ""

    prompt = f"""You are a senior supply chain risk analyst writing a brief for a supply chain executive.
    ...includes industry, company_context, all 5 sub-scores, commodity_changes, and biggest_risk...
    Rules: don't state the numeric scores directly, name the biggest risk specifically,
    mention at least one specific commodity or country, end with a forward-looking statement,
    write like you're briefing a busy VP - direct, no filler.
    """
    return _call_llm(prompt).strip()
```

No explicit model choice to make here — Groq's `llama-3.1-8b-instant` and Ollama's `llama3.2` are both fast, free, and more than capable of following the formatting rules above for a 3-4 sentence brief.

---

## The Recommendations Function

Recommendations are **templated, not freely AI-generated** — the AI calculated nothing here at all. The model picks the top 3 highest-scoring categories and fills in an industry-specific template:

```python
RECOMMENDATION_LIBRARY = {
    "supplier": {
        "title": "Qualify backup suppliers in alternative regions",
        "detail_template": "Given supplier concentration risk in {industry}, identify and qualify "
                            "1-2 backup suppliers in {alternative_region}. Aim to shift 15-20% of "
                            "volume within 6 months.",
        "priority": "High",
    },
    "commodity": {...}, "logistics": {...}, "geopolitical": {...}, "regulatory": {...},
}

ALTERNATIVE_REGIONS = {"Electronics": "Vietnam and India", "Pharma": "India and Ireland", ...}  # all 11 industries
PRIMARY_COMMODITIES = {"Electronics": "copper and semiconductor-related materials", ...}        # all 11 industries

def generate_recommendations(industry, result):
    """Top 3 recommendations, ranked by which sub-score is currently highest.

    Uses a fixed top-3 rather than a >60 threshold - real computed scores mostly
    sit in the moderate 25-55 range (see docs/03-RISK-SCORING.md), so a high
    threshold would return nothing most of the time.
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
```

This is a deliberate design choice, not a corner cut: a fixed library of pre-written, reviewed recommendation text — with the AI only choosing *which* template fits, never writing the recommendation itself — is more reliable than asking an LLM to invent supply-chain strategy advice from scratch every time.

---

## The Honesty Calibration: Company-Specific Functions

When a company name is entered, four functions can change what's displayed — all sharing one rule: **if the model isn't genuinely confident it has real, specific knowledge of the company, it must say so and change nothing**, rather than inventing plausible-sounding specifics.

1. **`detect_company_industry(company_name)`** — which of the 11 industries the company belongs to; the sidebar auto-syncs.
2. **`generate_company_score_adjustment(company_name, industry)`** — a -15 to +15 nudge per sub-score, with a `"known"` flag and a `"reasoning"` string that must name a *specific real fact* (e.g. "Apple sources advanced chips primarily from TSMC in Taiwan").
3. **`generate_company_sourcing_countries(company_name, industry)`** — the company's real, known sourcing countries (often more than the generic industry's 4-5).
4. **`generate_known_suppliers(company_name, industry)`** — specific named suppliers (e.g. "TSMC", "Foxconn") when genuinely known; feeds the High-Risk Suppliers list and the Supplier Compliance Status sanctions check.

**This calibration took real, found-by-testing iteration.** The first prompt version confidently fabricated detailed, plausible-sounding sourcing breakdowns for entirely made-up company names ("Globex Manufacturing Solutions," "ZX Quark Dynamics Inc"). The fix, used in all four prompts: explicitly instruct the model to treat generic-sounding or unfamiliar names as NOT known by default, and require it name a *specific, real fact* before marking anything as known — verified by testing against both real companies and deliberately fictional ones.

```python
def generate_company_score_adjustment(company_name, industry):
    prompt = f"""...
    First, decide: is "{company_name}" a real, specific company you can name verified,
    well-known facts about? Many names you are given will be small, obscure, or entirely
    made up. Do not guess or extrapolate from the name itself.

    If known, estimate adjustments from -15 to +15 per dimension using only real facts.

    Respond with ONLY a JSON object: {{"known": true/false, "supplier": number, ...,
    "reasoning": "one short sentence naming a specific real fact, or empty if not known"}}

    If not known with high confidence, set "known" to false and all adjustments to 0.
    """
    raw = _call_llm(prompt, temperature=0)
    # parsed, clamped to [-15, 15], defaults to known=False / all-zero on any parse error
```

Every company function fails closed the same way: a malformed response, a network error, or genuine uncertainty all resolve to "not known" rather than guessing.

---

## Cost

Both providers are free. Groq's free tier is generous enough for a portfolio-project's traffic; Ollama running locally costs nothing beyond your own machine's compute. There is no billing to manage, no credit card on file, and no cost-per-call calculation to do — which is also why this project doesn't need the `@st.cache_data` AI-response caching pattern just to control spend (it's still used, but for latency/UX, not cost).

---

## What Makes the AI Output Good vs. Generic

**Bad prompt (produces generic output):**
> "Summarize supply chain risks for Electronics."

**Good prompt (produces specific, useful output) — what's actually sent:**
> Industry, company context (if any), all 5 named sub-scores, real commodity % changes, and an explicit instruction to name the single biggest risk and at least one specific commodity or country, with formatting rules (length, no raw numbers, forward-looking close).

The difference is giving the model real, already-computed data and specific constraints — it's never asked to know things on its own, only to translate what's already been calculated. That's the professional way to use AI in enterprise software: **the AI translates; the model computes.**

Next: [docs/06-DEPLOYMENT.md](06-DEPLOYMENT.md) — How to put the app live on the internet for free.
