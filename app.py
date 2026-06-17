import streamlit as st
import plotly.graph_objects as go

from src.models.risk_engine import calculate_risk_score, WEIGHTS, get_risk_label
from src.data.geopolitical import COUNTRY_NAMES, get_country_risk
from src.data.commodity_prices import get_commodity_prices
from src.data.shipping import SHIPPING_STATUS
from src.models.logistics_risk import calculate_logistics_risk
from src.models.geopolitical_risk import calculate_geopolitical_risk, wb_score_to_risk
from src.ai.summary import (
    generate_risk_summary_safe,
    generate_recommendations,
    generate_company_context_safe,
    generate_company_score_adjustment,
    detect_company_industry_safe,
    generate_company_sourcing_countries_safe,
)

st.set_page_config(
    page_title="Supply Chain Risk Monitor",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

    html, body, [class*="css"], .stApp, .stMarkdown, p, div, span {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
    }

    /* Sidebar: dark slate for contrast against the light main content area */
    [data-testid="stSidebar"] {
        background-color: #0F172A;
    }
    [data-testid="stSidebar"] * {
        color: #E2E8F0 !important;
    }
    [data-testid="stSidebar"] label {
        color: #94A3B8 !important;
        font-weight: 600 !important;
        font-size: 0.8rem !important;
        text-transform: uppercase;
        letter-spacing: 0.04em;
    }
    [data-testid="stSidebar"] hr {
        border-color: #334155;
    }
    [data-testid="stSidebar"] input, [data-testid="stSidebar"] [data-baseweb="select"] > div {
        background-color: #1E293B !important;
        border-color: #334155 !important;
        color: #F1F5F9 !important;
    }

    /* Headings get tighter, bolder treatment than Streamlit's default */
    h1 {
        font-weight: 800 !important;
        letter-spacing: -0.02em !important;
        color: #0F172A !important;
    }
    h2, h3 {
        font-weight: 700 !important;
        letter-spacing: -0.01em !important;
        color: #1E293B !important;
        margin-top: 0.4em !important;
    }

    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 6px;
    }
    .stTabs [data-baseweb="tab"] {
        font-weight: 600;
        padding: 10px 18px;
        border-radius: 8px 8px 0 0;
    }

    /* Score / risk cards */
    .risk-card {
        background: #FFFFFF;
        border-radius: 14px;
        padding: 20px 22px;
        margin: 6px 0;
        box-shadow: 0 1px 3px rgba(15, 23, 42, 0.08), 0 1px 2px rgba(15, 23, 42, 0.04);
        border-left: 5px solid var(--card-color, #94A3B8);
        transition: box-shadow 0.2s ease, transform 0.2s ease;
    }
    .risk-card:hover {
        box-shadow: 0 6px 16px rgba(15, 23, 42, 0.10);
        transform: translateY(-2px);
    }
    .risk-card .risk-icon { font-size: 26px; margin-bottom: 8px; }
    .risk-card .risk-label {
        font-weight: 600; font-size: 13px; color: #64748B;
        text-transform: uppercase; letter-spacing: 0.04em;
    }
    .risk-card .risk-value { font-size: 38px; font-weight: 800; margin-top: 4px; line-height: 1.1; }

    /* AI text panels (risk brief, company note) */
    .note-card {
        border-radius: 14px;
        padding: 22px 24px;
        box-shadow: 0 1px 3px rgba(15, 23, 42, 0.08);
        line-height: 1.7;
        font-size: 15.5px;
    }

    /* Recommendation cards */
    .rec-card {
        background: #FFFFFF;
        border-radius: 12px;
        padding: 18px 20px;
        margin: 10px 0;
        box-shadow: 0 1px 3px rgba(15, 23, 42, 0.06);
        border: 1px solid #EEF2F7;
    }

    /* Tighter, more deliberate vertical rhythm between sections */
    div[data-testid="stVerticalBlock"] > div { margin-bottom: 0.15rem; }
    </style>
    """,
    unsafe_allow_html=True,
)

INDUSTRIES = ["Electronics", "Automotive", "Pharma", "Retail", "Food & Beverage"]


def get_risk_color(score):
    if score <= 30:
        return "#2ECC71"
    elif score <= 60:
        return "#F39C12"
    elif score <= 80:
        return "#E67E22"
    return "#E74C3C"


def get_country_name(code):
    return COUNTRY_NAMES.get(code, code)


# Plotly's choropleth matches countries far more reliably by ISO alpha-3 code than
# by English name string - "South Korea", "Taiwan", and "Malaysia" silently failed
# to match anything under locationmode="country names" during testing.
ALPHA2_TO_ALPHA3 = {
    "AD": "AND", "AE": "ARE", "AF": "AFG", "AG": "ATG", "AL": "ALB", "AM": "ARM",
    "AO": "AGO", "AR": "ARG", "AT": "AUT", "AU": "AUS", "AZ": "AZE", "BA": "BIH",
    "BD": "BGD", "BE": "BEL", "BF": "BFA", "BG": "BGR", "BH": "BHR", "BI": "BDI",
    "BJ": "BEN", "BN": "BRN", "BO": "BOL", "BR": "BRA", "BS": "BHS", "BT": "BTN",
    "BW": "BWA", "BY": "BLR", "BZ": "BLZ", "CA": "CAN", "CD": "COD", "CF": "CAF",
    "CG": "COG", "CH": "CHE", "CI": "CIV", "CL": "CHL", "CM": "CMR", "CN": "CHN",
    "CO": "COL", "CR": "CRI", "CU": "CUB", "CY": "CYP", "CZ": "CZE", "DE": "DEU",
    "DJ": "DJI", "DK": "DNK", "DO": "DOM", "DZ": "DZA", "EC": "ECU", "EE": "EST",
    "EG": "EGY", "ER": "ERI", "ES": "ESP", "ET": "ETH", "FI": "FIN", "FJ": "FJI",
    "FR": "FRA", "GA": "GAB", "GB": "GBR", "GE": "GEO", "GH": "GHA", "GM": "GMB",
    "GN": "GIN", "GQ": "GNQ", "GR": "GRC", "GT": "GTM", "GW": "GNB", "GY": "GUY",
    "HN": "HND", "HR": "HRV", "HT": "HTI", "HU": "HUN", "ID": "IDN", "IE": "IRL",
    "IL": "ISR", "IN": "IND", "IQ": "IRQ", "IR": "IRN", "IS": "ISL", "IT": "ITA",
    "JM": "JAM", "JO": "JOR", "JP": "JPN", "KE": "KEN", "KG": "KGZ", "KH": "KHM",
    "KP": "PRK", "KR": "KOR", "KW": "KWT", "KZ": "KAZ", "LA": "LAO", "LB": "LBN",
    "LK": "LKA", "LR": "LBR", "LS": "LSO", "LT": "LTU", "LU": "LUX", "LV": "LVA",
    "LY": "LBY", "MA": "MAR", "MD": "MDA", "ME": "MNE", "MG": "MDG", "MK": "MKD",
    "ML": "MLI", "MM": "MMR", "MN": "MNG", "MR": "MRT", "MT": "MLT", "MU": "MUS",
    "MW": "MWI", "MX": "MEX", "MY": "MYS", "MZ": "MOZ", "NA": "NAM", "NE": "NER",
    "NG": "NGA", "NI": "NIC", "NL": "NLD", "NO": "NOR", "NP": "NPL", "NZ": "NZL",
    "OM": "OMN", "PA": "PAN", "PE": "PER", "PG": "PNG", "PH": "PHL", "PK": "PAK",
    "PL": "POL", "PT": "PRT", "PY": "PRY", "QA": "QAT", "RO": "ROU", "RS": "SRB",
    "RU": "RUS", "RW": "RWA", "SA": "SAU", "SD": "SDN", "SE": "SWE", "SG": "SGP",
    "SI": "SVN", "SK": "SVK", "SL": "SLE", "SN": "SEN", "SO": "SOM", "SS": "SSD",
    "SV": "SLV", "SY": "SYR", "SZ": "SWZ", "TD": "TCD", "TG": "TGO", "TH": "THA",
    "TJ": "TJK", "TL": "TLS", "TM": "TKM", "TN": "TUN", "TR": "TUR", "TT": "TTO",
    "TW": "TWN", "TZ": "TZA", "UA": "UKR", "UG": "UGA", "US": "USA", "UY": "URY",
    "UZ": "UZB", "VE": "VEN", "VN": "VNM", "YE": "YEM", "ZA": "ZAF", "ZM": "ZMB",
    "ZW": "ZWE",
}


def hex_to_rgba(hex_color, alpha=0.13):
    """Plotly's fillcolor needs rgba(), not CSS-style 8-digit hex-with-alpha."""
    hex_color = hex_color.lstrip("#")
    r, g, b = int(hex_color[0:2], 16), int(hex_color[2:4], 16), int(hex_color[4:6], 16)
    return f"rgba({r},{g},{b},{alpha})"


@st.cache_data(ttl=3600, show_spinner=False)
def get_cached_risk_score(industry):
    return calculate_risk_score(industry)


@st.cache_data(ttl=3600, show_spinner=False)
def get_cached_company_adjustment(company_name, industry):
    return generate_company_score_adjustment(company_name, industry)


@st.cache_data(ttl=3600, show_spinner=False)
def get_cached_company_industry(company_name):
    return detect_company_industry_safe(company_name)


@st.cache_data(ttl=3600, show_spinner=False)
def get_cached_company_sourcing(company_name, industry):
    return generate_company_sourcing_countries_safe(company_name, industry)


@st.cache_data(ttl=3600, show_spinner=False)
def get_cached_commodity_prices(industry):
    return get_commodity_prices(industry)


@st.cache_data(ttl=3600, show_spinner=False)
def get_cached_logistics_risk():
    return calculate_logistics_risk()


@st.cache_data(ttl=3600, show_spinner=False)
def get_cached_geopolitical_risk(industry):
    return calculate_geopolitical_risk(industry)


def display_score_card(label, score, icon):
    color = get_risk_color(score)
    st.markdown(
        f"""
        <div class="risk-card" style="--card-color: {color};">
            <div class="risk-icon">{icon}</div>
            <div class="risk-label">{label}</div>
            <div class="risk-value" style="color: {color};">{score}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ---- SIDEBAR ----
with st.sidebar:
    st.title("Risk Monitor Settings")
    st.markdown("---")

    company_name = st.text_input(
        "Company Name (optional)",
        placeholder="e.g., Apple, Toyota, Pfizer",
        help="Enter a specific company - its industry is detected automatically",
    )

    # A company name determines its own industry automatically - typing "Apple" works
    # correctly no matter what the Industry dropdown is set to, instead of requiring the
    # user to also manually pick the matching industry (error-prone: e.g. picking
    # "Automotive" while typing "Apple" would silently score Apple as a car company).
    # This MUST run before the selectbox below is instantiated - Streamlit only allows
    # setting a keyed widget's session_state value before that widget is created, not after.
    detected_industry = None
    if company_name:
        with st.spinner(f"Identifying {company_name}'s industry..."):
            detected_industry = get_cached_company_industry(company_name)
        if detected_industry and st.session_state.get("industry_select") != detected_industry:
            st.session_state["industry_select"] = detected_industry

    industry = st.selectbox("Select Industry", options=INDUSTRIES, index=0, key="industry_select")

    time_horizon = st.selectbox(
        "Risk Time Horizon", options=["30 days", "90 days", "180 days"], index=1
    )

    st.markdown("---")
    st.caption("Data sources: FRED, Alpha Vantage, World Bank, NewsAPI")

# ---- HEADER ----
title_text = "Supply Chain Risk Monitor"
if company_name:
    title_text += f" — {company_name}"
st.title(title_text)

badges = f"""
    <span style="background:#EEF2FF; color:#4F46E5; padding:5px 14px; border-radius:20px; font-size:13px; font-weight:700;">{industry}</span>
    <span style="background:#F1F5F9; color:#475569; padding:5px 14px; border-radius:20px; font-size:13px; font-weight:700;">{time_horizon} horizon</span>
"""
if company_name and not detected_industry:
    badges += (
        '<span style="background:#FEF3C7; color:#92400E; padding:5px 14px; '
        'border-radius:20px; font-size:13px; font-weight:700;">'
        f"Industry not recognized for '{company_name}' - showing dropdown selection</span>"
    )

st.markdown(
    f"""<div style="display:flex; gap:8px; margin-top:-10px; margin-bottom:20px;">{badges}</div>""",
    unsafe_allow_html=True,
)

# ---- RISK SCORE SECTION ----
with st.spinner("Fetching live data and calculating risk scores..."):
    base_result = get_cached_risk_score(industry)

# Company name only nudges scores when the AI has real, specific knowledge of that
# company - otherwise it stays at the pure industry baseline. This keeps the dashboard
# honest: a made-up or obscure name can't silently inflate/deflate the displayed risk.
adjusted_sub_scores = dict(base_result["sub_scores"])
company_adjustment = None
if company_name:
    with st.spinner(f"Checking company-specific factors for {company_name}..."):
        company_adjustment = get_cached_company_adjustment(company_name, industry)
    if company_adjustment["known"]:
        for key in ("supplier", "commodity", "logistics", "geopolitical"):
            adjusted_sub_scores[key] = round(
                max(0, min(100, adjusted_sub_scores[key] + company_adjustment[key])), 1
            )

adjusted_total = round(sum(adjusted_sub_scores[key] * WEIGHTS[key] for key in WEIGHTS), 1)
result = {
    "industry": industry,
    "total": adjusted_total,
    "label": get_risk_label(adjusted_total),
    "sub_scores": adjusted_sub_scores,
    "details": base_result["details"],
}

st.markdown("## Overall Risk Assessment")

gauge_col, cards_col = st.columns([1, 2])

with gauge_col:
    fig = go.Figure(
        go.Indicator(
            mode="gauge+number",
            value=result["total"],
            number={"font": {"size": 48}},
            title={"text": "Overall Risk Score", "font": {"size": 18}},
            gauge={
                "axis": {"range": [0, 100], "tickwidth": 1},
                "bar": {"color": get_risk_color(result["total"])},
                "steps": [
                    {"range": [0, 30], "color": "#d5f5e3"},
                    {"range": [30, 60], "color": "#fef9e7"},
                    {"range": [60, 80], "color": "#fdebd0"},
                    {"range": [80, 100], "color": "#fadbd8"},
                ],
                "threshold": {
                    "line": {"color": "black", "width": 4},
                    "thickness": 0.75,
                    "value": result["total"],
                },
            },
        )
    )
    fig.update_layout(
        height=280,
        margin=dict(t=50, b=10, l=30, r=40),
        font=dict(family="Inter, sans-serif", color="#1E293B"),
    )
    st.plotly_chart(fig, use_container_width=True)

    color = get_risk_color(result["total"])
    st.markdown(
        f"<h3 style='text-align:center; color:{color}'>{result['label']}</h3>",
        unsafe_allow_html=True,
    )

with cards_col:
    row1_col1, row1_col2 = st.columns(2)
    row2_col1, row2_col2 = st.columns(2)

    with row1_col1:
        display_score_card("Supplier Concentration", result["sub_scores"]["supplier"], "🏭")
    with row1_col2:
        display_score_card("Commodity Price", result["sub_scores"]["commodity"], "📦")
    with row2_col1:
        display_score_card("Logistics & Shipping", result["sub_scores"]["logistics"], "🚢")
    with row2_col2:
        display_score_card("Geopolitical", result["sub_scores"]["geopolitical"], "🌍")

# ---- DETAIL TABS (placeholders for now) ----
st.markdown("---")
st.markdown("## Detailed Analysis")

tab1, tab2, tab3, tab4 = st.tabs(
    ["📈 Commodity Prices", "🚢 Shipping Routes", "🌍 Geopolitical Map", "📋 AI Summary & Recommendations"]
)

with tab1:
    st.markdown("### Commodity Price Trends")

    commodity_data = get_cached_commodity_prices(industry)

    for commodity_name, history in commodity_data.items():
        if len(history) < 2:
            st.warning(
                f"{commodity_name} price data is temporarily unavailable - this usually means "
                f"the free-tier API quota (25 requests/day) was reached. It will refresh on its own."
            )
            continue

        dates = [item["date"] for item in history]
        values = [item["value"] for item in history]
        pct_change = (values[-1] - values[0]) / values[0]
        line_color = "#E74C3C" if pct_change > 0 else "#2ECC71"

        fig = go.Figure()
        fig.add_trace(
            go.Scatter(
                x=dates,
                y=values,
                mode="lines",
                line=dict(color=line_color, width=2),
                fill="tozeroy",
                fillcolor=hex_to_rgba(line_color),
            )
        )
        fig.update_layout(
            title=f"{commodity_name} — {pct_change:+.1%} over shown period",
            height=220,
            margin=dict(t=40, b=20, l=40, r=20),
            showlegend=False,
            hovermode="x unified",
            font=dict(family="Inter, sans-serif", color="#1E293B"),
            plot_bgcolor="#FFFFFF",
            paper_bgcolor="#FFFFFF",
        )
        st.plotly_chart(fig, use_container_width=True)

with tab2:
    st.markdown("### Shipping Route Status")
    st.caption(
        "Baseline status is hand-curated and updated every 1-2 weeks. The 'news signal' "
        "column reflects a same-day check for unusual breaking coverage on that route."
    )

    status_colors = {"NORMAL": "#2ECC71", "ELEVATED": "#F39C12", "DISRUPTED": "#E67E22", "SEVERE": "#E74C3C"}
    logistics_result = get_cached_logistics_risk()

    for route_name, route_data in SHIPPING_STATUS.items():
        status = route_data["status"]
        color = status_colors.get(status, "#999")
        route_score = logistics_result["by_route"][route_name]

        col1, col2, col3, col4 = st.columns([3, 1, 1, 1.3])

        with col1:
            st.markdown(f"**{route_name}**")
            st.caption(route_data["summary"])

        with col2:
            st.markdown(f"<span style='color:{color}; font-weight:bold'>{status}</span>", unsafe_allow_html=True)
            st.caption(f"+{route_data['delay_days']}d delay, +{route_data['cost_premium_pct']}% cost")

        with col3:
            st.metric("Risk Score", route_score["final"])

        with col4:
            if route_score["alert_adjustment"] > 0:
                st.caption(f"⚠️ News signal: +{route_score['alert_adjustment']}")
            else:
                st.caption("No unusual news activity")

        st.markdown("---")

    st.metric("Overall Logistics Risk", logistics_result["score"])

with tab3:
    st.markdown(f"### Sourcing Risk Map — {industry}")

    geo_result = get_cached_geopolitical_risk(industry)
    by_country = geo_result["by_country"]

    # For a recognized company, show its own (often longer) real sourcing list instead
    # of the generic 4-5 country industry baseline - falls back to the industry baseline
    # if the company isn't recognized or the model has no specific knowledge of it.
    if company_name and detected_industry:
        with st.spinner(f"Looking up {company_name}'s sourcing countries..."):
            company_sourcing = get_cached_company_sourcing(company_name, industry)
        if company_sourcing:
            company_by_country = {}
            for item in company_sourcing:
                code = item["country_code"]
                try:
                    wb_data = get_country_risk(code)
                    risk = round(wb_score_to_risk(wb_data["value"]), 1)
                except Exception:
                    continue  # skip countries World Bank has no data for, rather than guessing
                company_by_country[code] = {
                    "name": item["country"],
                    "weight": item["share"] / 100,
                    "final": risk,
                    "product": item["product"],
                }
            if company_by_country:
                by_country = company_by_country

    mappable = {code: data for code, data in by_country.items() if code in ALPHA2_TO_ALPHA3}

    fig = go.Figure(
        data=go.Choropleth(
            locations=[ALPHA2_TO_ALPHA3[code] for code in mappable],
            locationmode="ISO-3",
            z=[data["final"] for data in mappable.values()],
            zmin=0,
            zmax=100,
            colorscale=[[0, "#2ECC71"], [0.3, "#F39C12"], [0.6, "#E67E22"], [1.0, "#E74C3C"]],
            marker_line_color="white",
            marker_line_width=0.5,
            colorbar_title="Risk Score",
        )
    )
    fig.update_layout(
        geo=dict(showframe=False, showcoastlines=True, projection_type="equirectangular"),
        height=400,
        margin=dict(t=10, b=10, l=0, r=0),
        font=dict(family="Inter, sans-serif", color="#1E293B"),
    )
    st.plotly_chart(fig, use_container_width=True)

    st.markdown("#### Sourcing Concentration Breakdown")
    if company_name and by_country is not geo_result["by_country"]:
        st.caption(f"All {len(by_country)} countries {company_name} is known to source from.")
    else:
        st.caption(f"All {len(by_country)} countries {industry} sources from, and what's actually sourced from each.")

    for code, data in sorted(by_country.items(), key=lambda x: x[1]["weight"], reverse=True):
        color = get_risk_color(data["final"])
        st.markdown(
            f"""
            <div class="rec-card" style="display:flex; justify-content:space-between; align-items:center; gap:16px;">
                <div style="flex:2;">
                    <div style="font-weight:700; color:#1E293B; font-size:15px;">{data['name']} ({code})</div>
                    <div style="color:#64748B; margin-top:4px; font-size:13.5px;">{data['product']}</div>
                </div>
                <div style="flex:1; text-align:center;">
                    <div style="font-weight:700; color:#1E293B; font-size:16px;">{data['weight'] * 100:.0f}%</div>
                    <div style="color:#94A3B8; font-size:11px; text-transform:uppercase; letter-spacing:0.03em;">of sourcing</div>
                </div>
                <div style="flex:1; text-align:center;">
                    <div style="font-weight:800; color:{color}; font-size:18px;">{data['final']}</div>
                    <div style="color:#94A3B8; font-size:11px; text-transform:uppercase; letter-spacing:0.03em;">risk score</div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

with tab4:
    commodity_changes = {
        name: (history[-1]["value"] - history[0]["value"]) / history[0]["value"] * 100
        for name, history in commodity_data.items()
        if len(history) >= 2
    }

    col_summary, col_rec = st.columns(2)

    with col_summary:
        st.markdown("### Brief")
        with st.spinner("Generating summary..."):
            ai_summary = generate_risk_summary_safe(industry, result, commodity_changes, company_name or None)
        st.markdown(
            f"""
            <div class="note-card" style="background: #F5F8FF; border-left: 5px solid #4F46E5;">
                {ai_summary}
            </div>
            """,
            unsafe_allow_html=True,
        )
        if company_name:
            st.markdown("#### Company Note")
            with st.spinner(f"Looking up {company_name}..."):
                company_note = generate_company_context_safe(company_name, industry)
            st.markdown(
                f"""
                <div class="note-card" style="background: #FFF9EB; border-left: 5px solid #F0AD4E; font-size: 14px;">
                    {company_note}
                </div>
                """,
                unsafe_allow_html=True,
            )

    with col_rec:
        st.markdown("### Recommended Actions")
        recommendations = generate_recommendations(industry, result)
        for i, rec in enumerate(recommendations, 1):
            st.markdown(
                f"""
                <div class="rec-card">
                    <div style="font-weight: 700; color: #1E293B; font-size: 15px;">{i}. {rec['title']}</div>
                    <div style="color: #475569; margin-top: 6px; line-height: 1.5;">{rec['detail']}</div>
                    <div style="color: #94A3B8; font-size: 12px; margin-top: 8px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.03em;">Priority: {rec['priority']}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
