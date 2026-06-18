Supply Chain Risk Monitor

---





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
- [x] Create `app.py` — the main Streamlit entry point
- [x] Build sidebar: industry dropdown, company text input, time horizon selector
- [x] Display overall risk score as a gauge chart (Plotly)
- [x] Display sub-score cards with color coding (grew from 4 to 5 cards as Regulatory & Trade was added)
- [x] Reference: [docs/04-BUILDING-THE-UI.md](docs/04-BUILDING-THE-UI.md)

### Day 3-4: Commodity Price Charts
- [x] Add commodity price tab
- [x] Display a line chart per commodity with Plotly (interactive, hoverable)
- [x] Show price change % over selected time horizon
- [x] Reference: [docs/04-BUILDING-THE-UI.md](docs/04-BUILDING-THE-UI.md) → Charts section

### Day 5: Shipping + Geopolitical Panels
- [x] Add shipping disruption panel — route names, delay status, cost premium
- [x] Add world map — Plotly choropleth map, countries colored by risk level
- [x] Reference: [docs/04-BUILDING-THE-UI.md](docs/04-BUILDING-THE-UI.md) → Map section

### Day 6: AI Summary + Recommendations
- [x] Add AI summary section — 3-4 sentence plain English risk brief
- [x] Add recommendations panel — 3 bullet points
- [x] Connect to an LLM — switched from the original plan's Anthropic/Claude to **Groq (deployed) / Ollama (local)**, since both are free, removing the only paid dependency in the whole stack
- [x] Reference: [docs/05-AI-SUMMARY.md](docs/05-AI-SUMMARY.md)

### Day 7: Full App Test
- [x] Run the full app locally: `streamlit run app.py`
- [x] Test all industries (grew from 5 to 11 - see Post-Launch below)
- [x] Fix any bugs, loading errors, or ugly UI spots
- **Done when:** The full app runs in your browser with no errors for any industry — confirmed

---

## Week 4 — Deploy, Polish, Launch

**Goal:** A live public URL that anyone can open.

### Day 1-2: Deploy to Streamlit Cloud
- [x] Push code to GitHub (public repo)
- [x] Sign up at streamlit.io/cloud (free)
- [x] Connect repo and deploy
- [x] Handle API key secrets securely in Streamlit Cloud settings
- [x] Reference: [docs/06-DEPLOYMENT.md](docs/06-DEPLOYMENT.md)

### Day 3-4: Polish
- [x] Fix any bugs that appeared in the deployed version
- [x] Clean up colors, fonts, spacing — make it look professional (multiple passes: card grid reflow, gauge sizing, mobile breakpoints, segmented-control contrast)
- [x] Add a loading spinner while data fetches
- [x] Add error messages if an API call fails (graceful degradation) — every external call (NewsAPI, kaleido, sanctions API) fails closed rather than crashing the page
- [x] Test on mobile — confirmed via Playwright at phone-width viewports

### Day 5: GitHub README
- [x] Write a compelling GitHub README with screenshots
- [x] Include the live URL prominently
- [x] List the tech stack and data sources

### Day 6-7: Launch
- [x] Update resume with the project and live URL
- **Done when:** Live URL is working — confirmed

---

## Post-Launch: Expanded to 7 Risk Categories
- [x] Added Currency/FX risk (`src/models/currency_risk.py`) using free FRED exchange rate series, volatility-based. Taiwan, Vietnam, Bangladesh, Argentina, and Ukraine have no free FRED FX series - those countries are excluded from the weighted calc rather than guessed.
- [x] Added Regulatory/Trade risk (`src/models/regulatory_risk.py`) - hand-curated baseline per industry + live tariff/trade-policy news-spike layer (reuses `news_alerts.py`'s infrastructure with a new keyword set).
- [x] Added Climate/Disaster risk (`src/models/climate_risk.py`) - hand-curated baseline per industry + live disaster-keyword news-spike layer.
- [x] Rebalanced `risk_engine.py` weights from 30/25/25/20 (4 categories) to 20/15/15/15/15/10/10 (7 categories) - supplier concentration stays the largest single factor.
- [x] Refactored `news_alerts.py` to accept a custom keyword set per call, so regulatory/climate signals reuse the same relative-spike detection and caching as the original country/route alerts instead of duplicating that logic.
- [x] Score cards in `app.py` now render as a 4+3 grid instead of 2x2 to fit all 7 categories.
- [x] **Reverted:** Currency/FX and Climate/Disaster removed again per user feedback after review - judged to add more noise than signal. Deleted `currency_risk.py`, `climate_risk.py`, `data/currency.py`, and `CLIMATE_KEYWORDS` outright rather than leaving them disabled-but-present. Back to 5 categories (Supplier 25%, Commodity/Logistics/Geopolitical 20% each, Regulatory 15%). Regulatory stayed since it was a separate, valued addition. Score cards now render as a single row of 5.

## Post-Launch: 11 Industries + Company-Specific AI Layer
- [x] Expanded from 5 to 11 industries (added Energy, Aerospace & Defense, Chemicals, Industrial Equipment & Machinery, IT, E-commerce), each with its own researched supplier-concentration score, sourcing-country breakdown, and regulatory baseline.
- [x] Added Titanium as a new tracked commodity (FRED `WPU102505`) since Aerospace & Defense needed it and none of the original 8 commodities applied.
- [x] Added a company name field (autocomplete from ~55 known companies, free-text accepted) with three AI-driven functions: industry auto-detection, a -15/+15 per-category score nudge based on real named facts, and a real sourcing-country list for recognized companies — all calibrated to default to "not known, change nothing" rather than fabricate plausible-sounding details for an unrecognized or made-up name.
- [x] Extensive UI polish: separated title from company badge, segmented control for time horizon, hover tooltips (via a custom "i" icon, since native `?` tooltips and Streamlit's `help=` rendered inconsistently), responsive CSS Grid for score cards (auto-fit instead of fixed Streamlit columns), mobile breakpoints for the gauge chart and sidebar.

## Post-Launch: Export to PDF & Excel
- [x] Added `src/export.py` generating a full report (all scores, AI summary, recommendations, detailed tables, and embedded chart/map images) as both PDF (fpdf2) and Excel (openpyxl) via two download buttons on the Summary tab.
- [x] Deliberately avoided `kaleido` at first to keep the dependency footprint small, representing scores via drawn colored boxes instead of chart images — **later reversed** once the user asked for charts/map images in the exports too. Added `kaleido` and made every chart-render call fail closed (returns `None`, export continues without that one image) since Streamlit Cloud's container doesn't always have the system Chrome libraries kaleido needs; added `packages.txt` with the required apt packages as a best-effort fix for that specific gap.
- [x] Fixed a real fpdf2 crash: AI-generated text often contains em-dashes/smart quotes that the core PDF font (Helvetica, latin-1 only) can't render — added a `_pdf_safe()` sanitizer.
- [x] Fixed an fpdf2 layout bug where `cell(0, ...)` means "extend to the right margin from the current x," not "full page width" — a stale `x` position from an earlier multi-line cell silently shrank the next cell's available width to near-zero and crashed. Fixed by explicitly resetting `x` and passing the real effective page width everywhere instead of `0`.
- [x] Added real company logos to the header badge (via Google's favicon service, mapped to each known company's actual domain) after Clearbit's logo CDN — the original choice — turned out to have a broken certificate chain on its dedicated subdomain.

## Post-Launch: Fixed Non-Deterministic AI Scoring
- [x] **Bug:** the same company could show a different risk score on different devices/sessions, because the LLM call behind the company-specific score adjustment had no fixed temperature or seed — every fresh call (different cache state, different device, different provider) could sample a different number for the same prompt.
- [x] Fixed by pinning `temperature=0` and `seed=42` for every AI call that produces a number or classification (industry detection, score adjustment, sourcing percentages, named suppliers) in `src/ai/summary.py`'s shared `_call_llm()`. Prose-only calls (the risk brief, recommendation detail text) keep their default temperature so they don't read as robotic.

## Post-Launch: New Dashboard Sections (Supplier / Logistics / Geographic & External Risk)
- [x] Added a **Supplier Risk** section: Supplier Risk Rating (reuses the existing baseline), Single Source Dependency (derived from the sourcing breakdown's top country share), and Supplier Compliance Status — a real check against the US Treasury's Consolidated Screening List via trade.gov's API (`src/data/sanctions.py`), requiring a free `TRADE_GOV_API_KEY`. Caught and fixed a real false positive during testing ("Apple" word-boundary-matched "ORIENTAL APPLE COMPANY PTE LTD") by switching from substring/word-boundary matching to exact-name matching only.
- [x] Added a **Logistics Risk** section: Shipment Delays and Port Congestion (both real, derived from existing route data), Transportation Risk Index (a relabeling of the existing Logistics & Shipping score), and On-Time Delivery Rate (explicitly labeled as an estimate derived from that score, since no free API publishes real carrier on-time data).
- [x] Added a **Geographic & External Risk** section: Natural Disaster Alerts, Weather Impact, and Regional Conflict Alerts (three new live NewsAPI keyword-spike checks against the top sourcing country, reusing `news_alerts.py`'s existing ratio-based spike detection with new keyword sets) plus Political/Regulatory Risks (an average of the existing Geopolitical and Regulatory scores).
- [x] Added then **removed** an "Executive Summary" section (Critical Risk Alerts, High-Risk Suppliers, Disruption Probability) after user feedback — the Overall Risk Score itself was kept (it has no other home in the PDF, unlike the web app's gauge chart), but the three sub-lists were cut everywhere (web app, PDF, Excel), with all now-dead computation cleaned up rather than left disabled.

## Post-Launch: Scoring Rework (Probability x Impact x Current State) + Per-Industry Weights
- [x] Reworked Commodity Price and Logistics & Shipping to genuinely compute Risk = Probability x Impact x Current State from existing real data (Commodity: volatility x trend x where today's price sits in its own range; Logistics: route status x typical delay days x cost premium), combined via **geometric mean** rather than a raw product — a raw product of three 0-1 fractions collapses toward 0 even when all three are merely "moderate," which would make every score look artificially low.
- [x] Supplier Concentration and Regulatory & Trade stayed as single hand-curated baselines — only one real structural number exists for each, so decomposing into fake P/I/CS sub-components would mean inventing two of three.
- [x] Added `WEIGHTS_BY_INDUSTRY` in `risk_engine.py` — weights can now vary per industry instead of one flat set across all 11. Electronics has a custom breakdown (Supplier 30% / Geopolitical 25% / Commodity 20% / Logistics 15% / Regulatory 10%); the other 10 industries fall back to the original flat 25/20/20/20/15 until industry-specific weights are provided.

## Post-Launch: Dashboard Visualization
- [x] Added a "Dashboard Visualization" area with a **Risk Ranking** chart (all 11 industries, sorted by overall score, as a horizontal stacked bar where each segment is a category's real weighted contribution) and a **Trend Analysis** chart (the current industry's overall score, snapshotted once per day to a local JSON file and plotted over time — starts with a single point and genuinely accumulates from when tracking began, since the score formula itself just changed and there's no real history to back-fill).
- [x] **Reverted:** a Risk Heat Map (industries x categories color grid) was the first version of the above — replaced with the stacked bar chart after user feedback that color-intensity grids are hard to compare precisely by eye. Also added, then removed after feedback: a Red/Amber/Green indicator row and a "Top 10 Risk Drivers" ranked list.
- [x] Fixed a kaleido/fpdf2 export bug where long industry names ("Industrial Equipment & Machinery") and the trailing trend-chart date label got clipped in the static PNG export, even though the same chart looked fine live in-browser — kaleido's static renderer doesn't auto-expand margins the way Plotly does interactively; fixed with explicit `automargin=True`.
- [x] Both new charts were added to the PDF/Excel exports too, as a new "Dashboard Visualization" section/sheet.

## Post-Launch: Visual Polish Pass
- [x] Restyled the Supplier/Logistics/Geographic Risk metrics as proper KPI cards (shadowed, colored left border, bold numbers) instead of plain inline-styled text, reusing the same CSS Grid pattern as the main 5 score cards.
- [x] Added a real-time Critical Risk Alert banner at the very top of the page (above the gauge), computed early in the script rather than buried in a tab.
- [x] Added a "Drill down into a category" expander under the main score cards, showing the underlying Probability/Impact/Current-State or base/alert/final breakdown per category.
- [x] Added supplier location markers (country-centroid dots, sized by sourcing share) layered on the existing choropleth map — deliberately country-level, not fabricated factory coordinates, since that's the actual precision of the underlying data.
- [x] Added a Dark Mode toggle as an isolated CSS override block, so the default light theme (and all its previously-tuned contrast fixes) stays untouched when off. Found and fixed a **pre-existing** bug while building this: a too-broad `h2, h3 { color: ... !important }` rule had been silently overriding the risk-level heading's intended color (green/amber/red) to dark slate this whole time — invisible against the light background, glaring against dark.

## Progress Tracker

| Phase | Status | Notes |
|------|--------|-------|
| Week 1 — Data Layer | Done | All 3 data files live and tested (commodity_prices.py, geopolitical.py, shipping.py) |
| Week 2 — Risk Scoring | Done | All sub-scores + risk_engine.py working across all 11 industries |
| Week 3 — Streamlit UI | Done | Full dashboard, all tabs, mobile-responsive |
| Week 4 — Deploy & Launch | Done | Live on Streamlit Cloud |
| Post-Launch — 11 industries + company AI layer | Done | |
| Post-Launch — PDF/Excel export | Done | |
| Post-Launch — Deterministic AI scoring fix | Done | |
| Post-Launch — Supplier/Logistics/Geographic Risk sections | Done | |
| Post-Launch — P x I x CS scoring rework + per-industry weights | Done | Only Electronics has custom weights so far - other 10 industries pending |
| Post-Launch — Dashboard Visualization (Risk Ranking + Trend) | Done | |
| Post-Launch — Visual polish (KPI cards, dark mode, alert banner, drill-down, map markers) | Done | |

Update this as you go. Change "Not started" to "In progress" or "Done".
