Supply Chain Risk Monitor

---

## Week 1 — Data Layer (APIs Working)

**Goal:** By end of week 1, you can type a command and get live data back. No UI yet. Just raw data in your terminal.

### Day 1-2: Environment Setup
- [x] Install Python (3.10+) if not installed
- [x] Install libraries: `pip install streamlit plotly pandas requests anthropic python-dotenv`
- [x] Create a `.env` file for storing API keys (never put keys in code)
- [x] Sign up for: FRED API, Alpha Vantage API, World Bank API (all free, takes 10 mins total)
- [x] Confirm each API works with a basic test call
- Reference: [docs/02-DATA-SOURCES.md](docs/02-DATA-SOURCES.md) for exact sign-up links and test calls

### Day 3-4: Commodity Price Data
- [x] Write `src/data/commodity_prices.py`
- [x] Function: `get_commodity_prices(industry)` returns a dict of commodity → price history
- [x] Test it: call the function for "Automotive" and print steel + copper prices to terminal
- [x] Test it for "Electronics" and get semiconductor proxy prices
- Reference: [docs/02-DATA-SOURCES.md](docs/02-DATA-SOURCES.md) → Commodity Prices section
- Note: Copper/Aluminum/Wheat/Corn/Cotton come back as monthly data (Alpha Vantage free tier limitation), not daily. Oil and Natural Gas are true daily. Account for this in Week 2 trend/volatility math.

### Day 5-6: Geopolitical & Shipping Data
- [x] Write `src/data/geopolitical.py`
- [x] Write `src/data/shipping.py`
- [x] Functions return structured data (Python dicts) ready for the scoring model
- [x] Test both: print outputs to terminal to confirm they work
- Note: World Bank's short indicator codes (e.g. `PV.EST`) are archived/dead. Use the live codes prefixed `GOV_WGI_` (e.g. `GOV_WGI_PV.EST`).

### Day 7: Cleanup & Checkpoint
- [x] All 3 data files working and tested
- [x] Data returned is clean (no errors, no missing values)
- [x] Review data against scoring needs (does the data match what the risk model expects?)

### Bonus: Fast Alert Layer (added after Week 1)
- [x] Write `src/data/news_alerts.py` using NewsAPI.org
- [x] Compares this week's risk-keyword mentions to each subject's own 30-day baseline (a ratio, not a raw count) — raw counts always pegged newsworthy countries like China at max risk and never flagged real spikes
- [x] Cached 24h per subject to stay well under NewsAPI's 100 requests/day free limit
- [x] Fixed a query-building bug in Week 2 where multi-term route queries (e.g. Red Sea OR Suez Canal) got nested inside an extra pair of quotes, silently turning a boolean OR query into a near-literal string match. An earlier "validated" Red Sea spike (1.43x) turned out to be an artifact of that bug, not a real signal - it reads as ~0.9x (no spike) with the corrected query. Lesson: always re-verify a "validated" result if the underlying query logic changes.
- [x] Added `MIN_RECENT_COUNT_FOR_ALERT` guardrail: quiet subjects with tiny baselines (e.g. 1.2 articles/week) can swing to a "3x spike" off pure sample noise (e.g. 1 -> 4 articles) with headlines unrelated to the actual route. Now requires a real volume of coverage before any adjustment fires, not just a big ratio.
- [x] Switched from full-text search (`q`) to headline-only search (`qInTitle`). Full-text search caused major false positives during the 2026 World Cup - articles about Mexico/Brazil/Argentina incidentally contained risk-sounding words deep in unrelated body text. Headline-only search is far more precise. Lowered `MIN_RECENT_COUNT_FOR_ALERT` from 8 to 3 to match the naturally smaller volumes this produces.
- [x] Fixed a second query bug: `"export ban"` in the keyword list wasn't quoted when joined into the query, so NewsAPI matched bare "ban" anywhere - including cricket score headlines ("BAN vs AUS") and an unrelated social-media-ban story, which had been inflating Bangladesh and Australia's scores to the +20 max. Now all multi-word keywords are quoted individually.
- Note: heavy iterative testing during development burned through NewsAPI's 100-requests/day free quota. This is expected during active debugging, not a production concern - `calculate_geopolitical_risk()` and `calculate_logistics_risk()` both catch NewsAPI failures and fall back to adjustment=0 (baseline-only score) rather than crashing.
- Purpose: sits on top of the slow-moving baselines (World Bank's annual political stability data, hand-curated shipping status) to catch breaking events between baseline refreshes. Gets wired into the Week 2 scoring formulas as an adjustment, similar to the `ACTIVE_TENSIONS` bonus concept in [docs/03-RISK-SCORING.md](docs/03-RISK-SCORING.md).
- **Done when:** You can run `python src/data/commodity_prices.py` and see real prices

---

## Week 2 — Risk Scoring Model

**Goal:** By end of week 2, you can call one function with an industry name and get back a complete risk score breakdown.

### Day 0: Package Setup
- [x] Added empty `__init__.py` to `src/`, `src/data/`, `src/models/`, `src/ai/` so model files can import data files with `from src.data.X import Y`
- [x] Run model files going forward with `python -m src.models.X` (from project root), not `python src\models\X.py` directly

### Day 1-2: Individual Sub-Scores
- [x] Write `src/models/supplier_risk.py` — calculates 0-100 supplier concentration score
- [x] Write `src/models/commodity_risk.py` — calculates 0-100 commodity price volatility score
- [x] Fixed the monthly-vs-daily issue flagged in Week 1: added `_filter_to_window()` to slice price history by real calendar date, not by "last 90 entries" (which would span 7+ years for monthly commodities like Copper/Wheat)
- Reference: [docs/03-RISK-SCORING.md](docs/03-RISK-SCORING.md) for exact formulas

### Day 3-4: Shipping + Geopolitical Sub-Scores
- [x] Write `src/models/logistics_risk.py` — calculates 0-100 shipping disruption score, combining the hand-curated baseline with the `news_alerts.py` fast layer
- [x] Write `src/models/geopolitical_risk.py` — calculates 0-100 geopolitical exposure score, combining World Bank baseline with the `news_alerts.py` fast layer
- [x] Added caching to `geopolitical.py` (7-day, since World Bank data is annual) - it didn't have any caching from Week 1, and would otherwise be called repeatedly for every country/industry combo
- Reference: [docs/03-RISK-SCORING.md](docs/03-RISK-SCORING.md) for exact formulas

### Day 5-6: Master Scoring Function
- [x] Write `src/models/risk_engine.py`
- [x] Function: `calculate_risk_score(industry)` returns all 5 scores (4 sub + 1 total)
- [x] Weights: Supplier 30%, Commodity 25%, Logistics 25%, Geopolitical 20%
- [x] Test with all 5 industries — scores came out lower than the pre-build guess (see [docs/03-RISK-SCORING.md](docs/03-RISK-SCORING.md) "Pre-Build Estimate vs. What Actually Got Computed")

### Day 7: Validate the Model
- [x] Electronics (48.0) scores higher than Food & Beverage (38.0) — PASS
- [ ] Automotive should flag high commodity risk (steel, aluminum, lithium) — did NOT happen with current real data. Automotive's commodity score (28.6) is actually one of the lowest of the 5 industries right now, because steel/aluminum trends are calm. This reflects genuine current market conditions, not a bug — the expectation itself was just a guess made before real data existed.
- [x] Documented the weighting/dilution effect honestly in [docs/03-RISK-SCORING.md](docs/03-RISK-SCORING.md) rather than silently leaving stale "expected ranges" that didn't match reality
- **Done when:** `calculate_risk_score("Electronics")` returns a believable score with all sub-scores — confirmed, returns 48.0 with a full breakdown

---

## Week 3 — Streamlit UI

**Goal:** By end of week 3, the full app runs locally in your browser with all features working.

### Day 1-2: App Skeleton + Risk Score Display
- [ ] Create `app.py` — the main Streamlit entry point
- [ ] Build sidebar: industry dropdown, company text input, time horizon selector
- [ ] Display overall risk score as a gauge chart (Plotly)
- [ ] Display 4 sub-score cards with color coding
- [ ] Reference: [docs/04-BUILDING-THE-UI.md](docs/04-BUILDING-THE-UI.md)

### Day 3-4: Commodity Price Charts
- [ ] Add commodity price tab
- [ ] Display a line chart per commodity with Plotly (interactive, hoverable)
- [ ] Show price change % over selected time horizon
- [ ] Reference: [docs/04-BUILDING-THE-UI.md](docs/04-BUILDING-THE-UI.md) → Charts section

### Day 5: Shipping + Geopolitical Panels
- [ ] Add shipping disruption panel — route names, delay status, cost premium
- [ ] Add world map — Plotly choropleth map, countries colored by risk level
- [ ] Reference: [docs/04-BUILDING-THE-UI.md](docs/04-BUILDING-THE-UI.md) → Map section

### Day 6: AI Summary + Recommendations
- [ ] Add AI summary section — 3-4 sentence plain English risk brief
- [ ] Add recommendations panel — 3 bullet points
- [ ] Connect to Anthropic API (Claude)
- [ ] Reference: [docs/05-AI-SUMMARY.md](docs/05-AI-SUMMARY.md)

### Day 7: Full App Test
- [ ] Run the full app locally: `streamlit run app.py`
- [ ] Test all 5 industries
- [ ] Fix any bugs, loading errors, or ugly UI spots
- **Done when:** The full app runs in your browser with no errors for any industry

---

## Week 4 — Deploy, Polish, Launch

**Goal:** A live public URL that anyone can open.

### Day 1-2: Deploy to Streamlit Cloud
- [ ] Push code to GitHub (public repo)
- [ ] Sign up at streamlit.io/cloud (free)
- [ ] Connect repo and deploy
- [ ] Handle API key secrets securely in Streamlit Cloud settings
- [ ] Reference: [docs/06-DEPLOYMENT.md](docs/06-DEPLOYMENT.md)

### Day 3-4: Polish
- [ ] Fix any bugs that appeared in the deployed version
- [ ] Clean up colors, fonts, spacing — make it look professional
- [ ] Add a loading spinner while data fetches
- [ ] Add error messages if an API call fails (graceful degradation)
- [ ] Test on mobile — recruiters may view it on their phone

### Day 5: GitHub README
- [ ] Write a compelling GitHub README with screenshots
- [ ] Include the live URL prominently
- [ ] Add a GIF or screenshot of the dashboard
- [ ] List the tech stack and data sources

### Day 6-7: Launch
- [ ] Record a 2-minute screen recording walking through the app
- [ ] Write LinkedIn post (template in [docs/07-RESUME-AND-PITCH.md](docs/07-RESUME-AND-PITCH.md))
- [ ] Update resume with the project and live URL
- [ ] Send the link to supply chain professionals you know for feedback
- **Done when:** Live URL is working and you've posted it on LinkedIn

---

## Progress Tracker

| Week | Status | Notes |
|------|--------|-------|
| Week 1 — Data Layer | Done | All 3 data files live and tested (commodity_prices.py, geopolitical.py, shipping.py) |
| Week 2 — Risk Scoring | Done | All 4 sub-scores + risk_engine.py working across all 5 industries. News-alert layer temporarily showing 0 (NewsAPI daily quota exhausted from testing) — will self-resolve when quota resets. |
| Week 3 — Streamlit UI | Not started | |
| Week 4 — Deploy & Launch | Not started | |

Update this as you go. Change "Not started" to "In progress" or "Done".
