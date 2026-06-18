# Building the UI — Streamlit Dashboard

This explains how Streamlit works, how to structure the dashboard, and exactly how to build each section. No web development experience required.

**This doc covers the original 4-card, 4-tab build and is kept as the "how Streamlit basics work" tutorial — the live `app.py` has grown well beyond it.** Read "What's Actually in app.py Now" below first for an accurate map of the current dashboard, then use the sections after it to understand the underlying Streamlit mechanics (sidebar, tabs, gauge charts, choropleth maps) that are still built the same way.

---

## What's Actually in app.py Now

The dashboard grew in this order; each addition is a real, working section in the live app:

1. **A real-time Critical Risk Alert banner** at the very top of the page (above the gauge) — computed early in the script, right after the overall score, so it doesn't depend on anything rendered later.
2. **The gauge chart + 5 score cards** (Supplier, Commodity, Logistics, Geopolitical, Regulatory) — same idea as the tutorial below, rendered via a CSS Grid wrapper (`repeat(auto-fit, minmax(180px, 1fr))`) instead of fixed Streamlit columns, so cards reflow responsively instead of just getting squished on narrow screens.
3. **A "Drill down into a category" expander** right below the cards — one `st.tabs()` per category showing the underlying Probability/Impact/Current-State or base/alert/final breakdown.
4. **Four tabs** (Commodity Prices, Shipping Routes, Geopolitical Map, Summary & Recommendations) — the Geopolitical Map now also plots supplier-location markers (country centroids, sized by sourcing share) on top of the choropleth.
5. **Inside the Summary & Recommendations tab**, in order: the AI Brief + Recommended Actions (the original design), then three new sections — **Supplier Risk**, **Logistics Risk**, **Geographic & External Risk** — each rendered as a row of KPI cards (`kpi_card_html()`, a smaller sibling of the main score-card style), then **Dashboard Visualization** (a Risk Ranking chart comparing all 11 industries, and a Trend Analysis chart of the current industry's score over time), then the **Export Report** buttons (PDF/Excel).
6. **A Dark Mode toggle** in the sidebar, implemented as a conditional CSS override block injected only when the toggle is on — the default theme's CSS is never touched.

See [docs/03-RISK-SCORING.md](03-RISK-SCORING.md) for what each new section's numbers actually mean, and [PLAN.md](../PLAN.md) for the full chronological history, including two features (an Executive Summary section, and a Risk Heat Map before it became the Risk Ranking bar chart) that were built, shipped, and then reverted after feedback.

This is just `app.py` — the app also has 6 more sidebar pages under `pages/` (SupplyIQ: Supply Chain Simulator, Demand Forecasting, Supplier Scorecard, Logistics & Route Optimizer, Cost Optimization, Executive Dashboard), built as a separate Streamlit multipage app extension and not covered by this doc. Streamlit auto-discovers anything in `pages/` and adds it to the sidebar with zero wiring required in `app.py` itself.

---

## What Streamlit Is (Plain English)

Streamlit is a Python library that turns Python scripts into web apps. You write normal Python, and Streamlit handles all the HTML, CSS, and JavaScript for you.

The mental model: every time a user interacts with the app (changes the industry dropdown, clicks a button), Streamlit re-runs your Python script from top to bottom. The output of that script becomes what they see on screen.

This is why Streamlit is unusual — it's not like a typical web app where you have separate front-end and back-end. It's one Python script. That simplicity is why it's perfect for this project.

---

## Install and First Test

```bash
pip install -r requirements.txt

# Test that it works
streamlit hello
```

This opens a browser with a demo app. If you see it, you're ready.

---

## Your App Entry Point: app.py

Create `app.py` in the root of your project. Everything starts here.

```python
import streamlit as st

# This MUST be the first Streamlit command in your script
st.set_page_config(
    page_title="Supply Chain Risk Monitor",
    page_icon="🔍",
    layout="wide",          # Uses full browser width
    initial_sidebar_state="expanded"
)

# After this, build the rest of the app
```

Run it anytime with:
```bash
streamlit run app.py
```

---

## The Sidebar (User Inputs)

The sidebar holds all the user controls. In Streamlit, you create sidebar elements with `st.sidebar`.

```python
with st.sidebar:
    st.title("Risk Monitor Settings")
    st.markdown("---")
    
    # Industry selector
    industry = st.selectbox(
        "Select Industry",
        options=["Electronics", "Automotive", "Pharma", "Retail", "Food & Beverage"],
        index=0  # Default to Electronics
    )
    
    # Company name (optional)
    company_name = st.text_input(
        "Company Name (optional)",
        placeholder="e.g., Apple, Toyota, Pfizer",
        help="Enter a specific company to contextualize the analysis"
    )
    
    # Time horizon
    time_horizon = st.selectbox(
        "Risk Time Horizon",
        options=["30 days", "90 days", "180 days"],
        index=1  # Default to 90 days
    )
    
    st.markdown("---")
    
    # Calculate button
    analyze_button = st.button(
        "Analyze Risk",
        type="primary",  # Makes it blue
        use_container_width=True
    )
    
    st.markdown("---")
    st.caption("Data updated: live from FRED, Alpha Vantage, World Bank APIs")
```

**How the sidebar controls work:**

When the user changes any control, Streamlit re-runs the whole script. The variables `industry`, `company_name`, and `time_horizon` get their new values automatically. You use them downstream in your calculations.

---

## The Main Header

```python
# Header section
col_title, col_date = st.columns([3, 1])

with col_title:
    title_text = f"Supply Chain Risk Monitor"
    if company_name:
        title_text += f" — {company_name}"
    st.title(title_text)
    st.caption(f"Industry: {industry} | Horizon: {time_horizon} | As of June 2026")

with col_date:
    st.metric("Analysis Date", "Jun 16, 2026")
```

---

## Loading State

When APIs are being called, show a spinner so the user knows something is happening:

```python
with st.spinner("Fetching live data and calculating risk scores..."):
    scores = calculate_risk_score(industry)
    commodity_data = get_commodity_prices(industry)
    ai_summary = generate_risk_summary(industry, scores, commodity_data)
```

---

## Section 1: Risk Score Gauge + Sub-Score Cards

This is the top of the dashboard. A big gauge chart on the left, four metric cards on the right.

```python
# ---- OVERALL RISK SCORE SECTION ----
st.markdown("## Overall Risk Assessment")

gauge_col, cards_col = st.columns([1, 2])

with gauge_col:
    # Build a gauge chart with Plotly
    import plotly.graph_objects as go
    
    fig = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=scores["total"],
        number={"font": {"size": 48}},
        title={"text": "Overall Risk Score", "font": {"size": 18}},
        delta={"reference": 50, "increasing": {"color": "red"}, "decreasing": {"color": "green"}},
        gauge={
            "axis": {"range": [0, 100], "tickwidth": 1},
            "bar": {"color": get_risk_color(scores["total"])},
            "steps": [
                {"range": [0, 30], "color": "#d5f5e3"},    # Light green
                {"range": [30, 60], "color": "#fef9e7"},   # Light yellow
                {"range": [60, 80], "color": "#fdebd0"},   # Light orange
                {"range": [80, 100], "color": "#fadbd8"}   # Light red
            ],
            "threshold": {
                "line": {"color": "black", "width": 4},
                "thickness": 0.75,
                "value": scores["total"]
            }
        }
    ))
    
    fig.update_layout(height=280, margin=dict(t=50, b=10, l=20, r=20))
    st.plotly_chart(fig, use_container_width=True)
    
    # Risk label below gauge
    risk_level, risk_color = get_risk_label(scores["total"])
    st.markdown(f"<h3 style='text-align:center; color:{risk_color}'>{risk_level}</h3>", unsafe_allow_html=True)

with cards_col:
    # Four sub-score metric cards in a 2x2 grid
    row1_col1, row1_col2 = st.columns(2)
    row2_col1, row2_col2 = st.columns(2)
    
    with row1_col1:
        display_score_card("Supplier Concentration", scores["supplier"], "🏭")
    
    with row1_col2:
        display_score_card("Commodity Price", scores["commodity"], "📦")
    
    with row2_col1:
        display_score_card("Logistics & Shipping", scores["logistics"], "🚢")
    
    with row2_col2:
        display_score_card("Geopolitical", scores["geopolitical"], "🌍")
```

**The score card helper function:**

```python
def display_score_card(label, score, icon):
    color = get_risk_color(score)
    risk_level, _ = get_risk_label(score)
    
    st.markdown(f"""
        <div style="
            background: {color}22;
            border-left: 4px solid {color};
            border-radius: 8px;
            padding: 16px;
            margin: 4px 0;
        ">
            <div style="font-size: 24px">{icon}</div>
            <div style="font-weight: bold; font-size: 14px; color: #333">{label}</div>
            <div style="font-size: 36px; font-weight: bold; color: {color}">{score}</div>
            <div style="font-size: 12px; color: {color}">{risk_level}</div>
        </div>
    """, unsafe_allow_html=True)
```

---

## Section 2: Tabbed Detail Panels

Use Streamlit tabs to organize the detailed content:

```python
st.markdown("---")
st.markdown("## Detailed Analysis")

tab1, tab2, tab3, tab4 = st.tabs([
    "📈 Commodity Prices",
    "🚢 Shipping Routes",
    "🌍 Geopolitical Map",
    "📋 Summary & Recommendations"
])
```

---

## Tab 1: Commodity Price Charts

```python
with tab1:
    st.markdown("### Commodity Price Trends")
    st.caption(f"90-day price history for key {industry} commodities")
    
    # Get commodity data
    commodities = get_commodity_prices_for_industry(industry)
    
    for commodity_name, price_data in commodities.items():
        # price_data is a list of {date, value} dicts
        
        # Build Plotly line chart
        fig = go.Figure()
        
        dates = [item["date"] for item in price_data]
        values = [float(item["value"]) for item in price_data if item["value"] != "."]
        
        # Color the line based on trend (red if up, green if down)
        pct_change = (values[-1] - values[0]) / values[0]
        line_color = "#E74C3C" if pct_change > 0 else "#2ECC71"
        
        fig.add_trace(go.Scatter(
            x=dates,
            y=values,
            mode="lines",
            name=commodity_name,
            line=dict(color=line_color, width=2),
            fill="tozeroy",
            fillcolor=f"{line_color}22"
        ))
        
        fig.update_layout(
            title=f"{commodity_name} — {pct_change:+.1%} over 90 days",
            height=200,
            margin=dict(t=40, b=20, l=40, r=20),
            showlegend=False,
            hovermode="x unified"
        )
        
        st.plotly_chart(fig, use_container_width=True)
```

---

## Tab 2: Shipping Disruptions

```python
with tab2:
    st.markdown("### Shipping Route Status")
    
    from src.data.shipping import SHIPPING_STATUS
    
    for route_name, route_data in SHIPPING_STATUS.items():
        status = route_data["status"]
        
        # Color coding for status
        status_colors = {
            "NORMAL": "#2ECC71",
            "ELEVATED": "#F39C12",
            "DISRUPTED": "#E67E22",
            "SEVERE": "#E74C3C"
        }
        color = status_colors.get(status, "#999")
        
        # Build a status row
        col1, col2, col3, col4 = st.columns([3, 1, 1, 2])
        
        with col1:
            st.markdown(f"**{route_name}**")
            st.caption(route_data["summary"])
        
        with col2:
            st.markdown(f"<span style='color:{color}; font-weight:bold'>{status}</span>", unsafe_allow_html=True)
        
        with col3:
            if route_data["delay_days"] > 0:
                st.metric("Added Delay", f"+{route_data['delay_days']}d")
            else:
                st.metric("Added Delay", "None")
        
        with col4:
            if route_data["cost_premium_pct"] > 0:
                st.metric("Cost Premium", f"+{route_data['cost_premium_pct']}%")
            else:
                st.metric("Cost Premium", "Normal")
        
        st.markdown("---")
```

---

## Tab 3: Geopolitical World Map

This is the most visually impressive part of the app. A world map with countries colored by risk level.

```python
with tab3:
    st.markdown(f"### Sourcing Risk Map — {industry}")
    st.caption("Country color = combined political stability + active trade tension risk")
    
    from src.models.geopolitical_risk import INDUSTRY_SOURCING, calculate_country_risk
    
    sourcing = INDUSTRY_SOURCING[industry]
    
    # Build data for the map
    countries = list(sourcing.keys())
    weights = list(sourcing.values())
    risks = [calculate_country_risk(c) for c in countries]
    
    # Create choropleth map
    fig = go.Figure(data=go.Choropleth(
        locations=countries,
        z=risks,
        zmin=0,
        zmax=100,
        colorscale=[
            [0, "#2ECC71"],     # Green at 0
            [0.3, "#F39C12"],   # Yellow at 30
            [0.6, "#E67E22"],   # Orange at 60
            [1.0, "#E74C3C"]    # Red at 100
        ],
        marker_line_color="white",
        marker_line_width=0.5,
        colorbar_title="Risk Score"
    ))
    
    fig.update_layout(
        geo=dict(
            showframe=False,
            showcoastlines=True,
            projection_type="equirectangular"
        ),
        height=400,
        margin=dict(t=10, b=10, l=0, r=0)
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Show sourcing breakdown table below the map
    st.markdown("#### Sourcing Concentration Breakdown")
    
    for country, weight in sorted(sourcing.items(), key=lambda x: x[1], reverse=True):
        risk = calculate_country_risk(country)
        color = get_risk_color(risk)
        
        col_country, col_share, col_risk = st.columns([2, 1, 1])
        with col_country:
            st.write(f"**{get_country_name(country)}** ({country})")
        with col_share:
            st.write(f"{weight*100:.0f}% of sourcing")
        with col_risk:
            st.markdown(f"<span style='color:{color}; font-weight:bold'>{risk:.0f}/100</span>", unsafe_allow_html=True)
```

---

## Tab 4: Summary + Recommendations

```python
with tab4:
    col_summary, col_rec = st.columns([1, 1])
    
    with col_summary:
        st.markdown("### AI Risk Brief")
        st.markdown(f"""
            <div style="
                background: #f8f9fa;
                border-left: 4px solid #3498db;
                border-radius: 8px;
                padding: 20px;
                font-size: 16px;
                line-height: 1.6;
            ">
                {ai_summary}
            </div>
        """, unsafe_allow_html=True)
        st.caption("AI-generated. Based on current market data.")  # live app uses Groq/Ollama, see docs/05-AI-SUMMARY.md
    
    with col_rec:
        st.markdown("### Recommended Actions")
        
        recommendations = generate_recommendations(industry, scores)
        
        for i, rec in enumerate(recommendations, 1):
            st.markdown(f"""
                <div style="
                    background: white;
                    border: 1px solid #ddd;
                    border-radius: 8px;
                    padding: 16px;
                    margin: 8px 0;
                ">
                    <div style="font-weight: bold; color: #2c3e50">{i}. {rec['title']}</div>
                    <div style="color: #555; margin-top: 6px">{rec['detail']}</div>
                    <div style="color: #888; font-size: 12px; margin-top: 6px">Priority: {rec['priority']}</div>
                </div>
            """, unsafe_allow_html=True)
```

---

## Helper Functions (Put These at Top of app.py)

```python
def get_risk_label(score):
    if score <= 30:
        return "Low Risk", "#2ECC71"
    elif score <= 60:
        return "Moderate Risk", "#F39C12"
    elif score <= 80:
        return "High Risk", "#E67E22"
    else:
        return "Critical Risk", "#E74C3C"

def get_risk_color(score):
    _, color = get_risk_label(score)
    return color

COUNTRY_NAMES = {
    "CN": "China", "TW": "Taiwan", "KR": "South Korea",
    "VN": "Vietnam", "MY": "Malaysia", "IN": "India",
    "MX": "Mexico", "JP": "Japan", "DE": "Germany",
    "BD": "Bangladesh", "US": "United States", "BR": "Brazil",
    "AR": "Argentina", "AU": "Australia", "UA": "Ukraine",
    "IE": "Ireland", "SG": "Singapore"
}

def get_country_name(code):
    return COUNTRY_NAMES.get(code, code)
```

---

## Running the App

```bash
# Run locally
streamlit run app.py

# The browser opens automatically at http://localhost:8501
# Hot reload: save app.py and the browser updates automatically
```

**Common issues:**

- **Slow loading:** Your API calls are taking too long. Add caching (see [docs/02-DATA-SOURCES.md](02-DATA-SOURCES.md) → Caching section).
- **"No module named X" error:** Run `pip install X` for whatever is missing.
- **API key error:** Double-check your `.env` file and that `load_dotenv()` is called at the top of app.py.
- **Charts not showing:** You need `st.plotly_chart(fig, use_container_width=True)` — don't just call `fig.show()` like in a Jupyter notebook.

Next: [docs/05-AI-SUMMARY.md](05-AI-SUMMARY.md) — How the AI summary and recommendations work in detail.
