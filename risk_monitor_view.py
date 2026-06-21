import streamlit as st
import plotly.graph_objects as go

from src.models.risk_engine import calculate_risk_score, get_weights, get_risk_label
from src.data.geopolitical import COUNTRY_NAMES, get_country_risk
from src.data.commodity_prices import get_commodity_prices
from src.data.shipping import SHIPPING_STATUS, ROUTE_WEIGHTS
from src.models.logistics_risk import calculate_logistics_risk
from src.models.geopolitical_risk import calculate_geopolitical_risk, wb_score_to_risk
from src.ai.summary import (
    generate_risk_summary_safe,
    generate_recommendations,
    generate_company_context_safe,
    generate_company_score_adjustment,
    detect_company_industry_safe,
    generate_company_sourcing_countries_safe,
    generate_known_suppliers_safe,
)
from src.export import generate_excel_report, generate_pdf_report
from src.charts import (
    build_commodity_chart, build_geo_choropleth, ALPHA2_TO_ALPHA3, hex_to_rgba,
    build_risk_ranking_chart, build_score_trend_chart, RISK_CATEGORY_LABELS,
)
from src.data.sanctions import check_sanctions_status_safe
from src.data.news_alerts import get_country_disaster_alert, get_country_weather_alert, get_country_conflict_alert
from src.data.score_history import record_score_snapshot, get_score_history

st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

    html, body, .stApp, .stMarkdown, p {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
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

    /* Segmented control (Risk Time Horizon buttons) - unselected options default to a
       low-opacity style that's nearly invisible against the dark sidebar background. */
    [data-testid="stSidebar"] button[data-testid="stBaseButton-segmented_control"] {
        background-color: #1E293B !important;
        border-color: #334155 !important;
        opacity: 1 !important;
    }
    [data-testid="stSidebar"] button[data-testid="stBaseButton-segmented_control"] p {
        color: #E2E8F0 !important;
        opacity: 1 !important;
    }
    [data-testid="stSidebar"] button[data-testid="stBaseButton-segmented_controlActive"] {
        background-color: #4F46E5 !important;
        border-color: #4F46E5 !important;
        opacity: 1 !important;
    }
    [data-testid="stSidebar"] button[data-testid="stBaseButton-segmented_controlActive"] p {
        color: #FFFFFF !important;
        opacity: 1 !important;
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
        margin-top: 0.4em !important;
    }
    /* Excludes the risk-level heading ("Moderate Risk" etc.), which sets its own
       inline color matching the risk score - this rule was unintentionally
       clobbering that color to dark slate regardless of the actual risk level,
       a bug that was hard to notice in light mode but glaring in dark mode. */
    h2:not([style]), h3:not([style]) {
        color: #1E293B !important;
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
        font-weight: 600; font-size: 12px; color: #64748B;
        text-transform: uppercase; letter-spacing: 0.02em;
        word-break: keep-all; overflow-wrap: normal;
    }
    .risk-card .risk-value { font-size: 38px; font-weight: 800; margin-top: 4px; line-height: 1.1; }

    /* Secondary KPI cards (Supplier/Logistics/Geographic Risk metrics) - same
       visual language as .risk-card but smaller, since these sit one level below
       the 5 main category cards in the visual hierarchy. Styled like a BI-dashboard
       tile: colored top accent bar, soft corner watermark, hover lift. */
    .kpi-card {
        background: linear-gradient(150deg, #FFFFFF 0%, #FAFBFF 100%);
        border-radius: 16px;
        padding: 18px 20px 16px;
        margin: 6px 0;
        box-shadow: 0 2px 6px rgba(15, 23, 42, 0.06), 0 1px 2px rgba(15, 23, 42, 0.04);
        border: 1px solid #F1F5F9;
        border-top: 4px solid var(--card-color, #94A3B8);
        height: 100%;
        position: relative;
        overflow: hidden;
        transition: box-shadow 0.2s ease, transform 0.2s ease;
    }
    .kpi-card:hover {
        box-shadow: 0 10px 22px rgba(15, 23, 42, 0.12);
        transform: translateY(-3px);
    }
    .kpi-card::before {
        content: "";
        position: absolute;
        top: -30px; right: -30px;
        width: 90px; height: 90px;
        border-radius: 50%;
        background: var(--card-color, #94A3B8);
        opacity: 0.07;
    }
    .kpi-card .kpi-label {
        font-weight: 700; font-size: 11.5px; color: #64748B;
        text-transform: uppercase; letter-spacing: 0.06em;
        position: relative; z-index: 1;
    }
    .kpi-card .kpi-value {
        font-size: 30px; font-weight: 800; margin-top: 8px; line-height: 1.1;
        position: relative; z-index: 1;
    }
    .kpi-card .kpi-caption {
        font-size: 12.5px; color: #94A3B8; margin-top: 8px; line-height: 1.45;
        position: relative; z-index: 1;
    }

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

    /* The gauge container is fixed at 360px to avoid Plotly's number/arc overlapping
       when a flexible column squishes it - but on real phone-width screens, 360px is
       wider than the available space and would overflow off-screen. Shrink it down
       at narrow breakpoints instead (the Plotly chart inside uses width="stretch",
       so it fills whatever size this container ends up being). */
    @media (max-width: 600px) {
        .st-key-gauge_container { width: min(280px, 85vw) !important; }
    }
    </style>
    """,
    unsafe_allow_html=True,
)

INDUSTRIES = [
    "Electronics", "Automotive", "Pharma", "Retail", "Food & Beverage",
    "Energy", "Aerospace & Defense", "Chemicals", "Industrial Equipment & Machinery",
    "IT", "E-commerce",
]

# A starting list of well-known companies spanning all 11 industries, so the company
# name field can suggest options as you type. This is just a convenience list, not a
# restriction - accept_new_options=True on the selectbox lets you type any company at
# all, which the AI detection/adjustment layer handles the same way either way.
KNOWN_COMPANIES = [
    "Apple", "Samsung", "Sony", "LG", "Dell", "HP", "Lenovo",
    "Microsoft", "Google", "IBM", "Oracle", "Cisco", "Intel", "Nvidia",
    "Boeing", "Lockheed Martin", "Airbus", "Raytheon", "Northrop Grumman",
    "Pfizer", "Johnson & Johnson", "Moderna", "Merck", "Novartis", "AstraZeneca",
    "Toyota", "Ford", "General Motors", "Tesla", "Honda", "Volkswagen", "BMW",
    "ExxonMobil", "Chevron", "Shell", "BP", "Saudi Aramco",
    "Walmart", "Target", "Costco", "Home Depot",
    "Amazon", "eBay", "Alibaba", "Shopify",
    "Caterpillar", "Deere & Company", "Siemens", "General Electric",
    "Dow", "DuPont", "BASF",
    "Coca-Cola", "PepsiCo", "Nestle", "Unilever", "Kraft Heinz",
]

# Real corporate domains for the curated list above, used to fetch each company's
# favicon (via Google's favicon service) as a stand-in for its logo. Deliberately only
# covers this hand-picked list rather than guessing a domain for freely-typed companies -
# a wrong guess would either silently show a stranger's logo or a broken image, neither
# of which is worth the convenience for the long tail of typed-in names.
COMPANY_LOGO_DOMAINS = {
    "Apple": "apple.com", "Samsung": "samsung.com", "Sony": "sony.com", "LG": "lg.com",
    "Dell": "dell.com", "HP": "hp.com", "Lenovo": "lenovo.com",
    "Microsoft": "microsoft.com", "Google": "google.com", "IBM": "ibm.com",
    "Oracle": "oracle.com", "Cisco": "cisco.com", "Intel": "intel.com", "Nvidia": "nvidia.com",
    "Boeing": "boeing.com", "Lockheed Martin": "lockheedmartin.com", "Airbus": "airbus.com",
    "Raytheon": "rtx.com", "Northrop Grumman": "northropgrumman.com",
    "Pfizer": "pfizer.com", "Johnson & Johnson": "jnj.com", "Moderna": "modernatx.com",
    "Merck": "merck.com", "Novartis": "novartis.com", "AstraZeneca": "astrazeneca.com",
    "Toyota": "toyota.com", "Ford": "ford.com", "General Motors": "gm.com", "Tesla": "tesla.com",
    "Honda": "honda.com", "Volkswagen": "vw.com", "BMW": "bmw.com",
    "ExxonMobil": "exxonmobil.com", "Chevron": "chevron.com", "Shell": "shell.com",
    "BP": "bp.com", "Saudi Aramco": "aramco.com",
    "Walmart": "walmart.com", "Target": "target.com", "Costco": "costco.com", "Home Depot": "homedepot.com",
    "Amazon": "amazon.com", "eBay": "ebay.com", "Alibaba": "alibaba.com", "Shopify": "shopify.com",
    "Caterpillar": "caterpillar.com", "Deere & Company": "deere.com",
    "Siemens": "siemens.com", "General Electric": "ge.com",
    "Dow": "dow.com", "DuPont": "dupont.com", "BASF": "basf.com",
    "Coca-Cola": "coca-colacompany.com", "PepsiCo": "pepsico.com", "Nestle": "nestle.com",
    "Unilever": "unilever.com", "Kraft Heinz": "kraftheinzcompany.com",
}


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


def get_on_time_delivery_estimate(logistics_score):
    """Derives an estimated on-time delivery rate from the logistics risk score -
    there's no carrier/logistics-provider API behind this (no free one publishes
    real on-time performance data), so this is explicitly an estimate, not a
    measured statistic. Floored at 60% since even severe disruptions rarely push
    real-world on-time rates to literal 0%."""
    return max(60.0, round(100 - logistics_score * 0.4, 1))


def get_alert_band(adjustment):
    """Converts a news-spike adjustment (0-20, see news_alerts.ratio_to_adjustment)
    into a qualitative band for display."""
    if adjustment >= 12:
        return "High", "#E74C3C"
    elif adjustment >= 6:
        return "Elevated", "#F39C12"
    elif adjustment > 0:
        return "Watch", "#F0AD4E"
    return "Normal", "#2ECC71"




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
def get_cached_known_suppliers(company_name, industry):
    return generate_known_suppliers_safe(company_name, industry)


@st.cache_data(ttl=3600, show_spinner=False)
def get_cached_sanctions_status(entity_name):
    return check_sanctions_status_safe(entity_name)


_EMPTY_ALERT = {"recent_count": 0, "baseline_weekly_rate": 0, "ratio": 0, "adjustment": 0, "sample_headlines": []}


@st.cache_data(ttl=3600, show_spinner=False)
def get_cached_disaster_alert(country_name):
    try:
        return get_country_disaster_alert(country_name)
    except Exception:
        return _EMPTY_ALERT  # NewsAPI hiccup/rate limit shouldn't break the whole page


@st.cache_data(ttl=3600, show_spinner=False)
def get_cached_weather_alert(country_name):
    try:
        return get_country_weather_alert(country_name)
    except Exception:
        return _EMPTY_ALERT


@st.cache_data(ttl=3600, show_spinner=False)
def get_cached_conflict_alert(country_name):
    try:
        return get_country_conflict_alert(country_name)
    except Exception:
        return _EMPTY_ALERT


@st.cache_data(ttl=3600, show_spinner=False)
def get_cached_company_sourcing(company_name, industry):
    return generate_company_sourcing_countries_safe(company_name, industry)


@st.cache_data(ttl=3600, show_spinner=False)
def get_cached_commodity_prices(industry):
    return get_commodity_prices(industry)


@st.cache_data(ttl=3600, show_spinner="Building PDF report...")
def get_cached_pdf_report(*args):
    return generate_pdf_report(*args)


@st.cache_data(ttl=3600, show_spinner="Building Excel report...")
def get_cached_excel_report(*args):
    return generate_excel_report(*args)


@st.cache_data(ttl=3600, show_spinner=False)
def get_cached_logistics_risk():
    return calculate_logistics_risk()


@st.cache_data(ttl=3600, show_spinner=False)
def get_cached_geopolitical_risk(industry):
    return calculate_geopolitical_risk(industry)


def info_icon(tooltip_text):
    return (
        f'<span title="{tooltip_text}" style="'
        f'display:inline-flex; align-items:center; justify-content:center; '
        f'width:15px; height:15px; border-radius:50%; background:#CBD5E1; color:#fff; '
        f'font-size:10px; font-weight:700; font-style:italic; font-family:Georgia,serif; '
        f'cursor:pointer; margin-left:5px; vertical-align:middle;">i</span>'
    )


def score_card_html(label, score, icon, description=None):
    """Returns the card's HTML (doesn't render it) so multiple cards can be combined
    into one CSS Grid container - this lets the grid reflow card count per row based
    on actual available width (auto-fit), instead of Streamlit's fixed-ratio columns
    which just get uncomfortably narrow at small screen sizes rather than reflowing.
    """
    color = get_risk_color(score)
    risk_text = get_risk_label(score)
    tooltip = info_icon(description) if description else ""
    return (
        f'<div class="risk-card" style="--card-color: {color};">'
        f'<div class="risk-icon">{icon}</div>'
        f'<div class="risk-label">{label}{tooltip}</div>'
        f'<div class="risk-value" style="color: {color};">{score}</div>'
        f'<div style="font-size: 13px; font-weight: 700; color: {color}; margin-top: 2px;">{risk_text}</div>'
        f'</div>'
    )


def kpi_card_html(label, value_html, caption=None, color="#94A3B8"):
    """Same visual language as score_card_html's grid cards, for the secondary
    metrics added across Supplier/Logistics/Geographic & External Risk - so those
    sections read as KPI cards too, not plain inline text."""
    caption_html = f'<div class="kpi-caption">{caption}</div>' if caption else ""
    return (
        f'<div class="kpi-card" style="--card-color: {color};">'
        f'<div class="kpi-label">{label}</div>'
        f'<div class="kpi-value" style="color: {color};">{value_html}</div>'
        f'{caption_html}'
        f'</div>'
    )


# ---- SIDEBAR ----
with st.sidebar:
    st.title("Risk Monitor Settings")
    dark_mode = st.toggle("Dark Mode", value=False)

    if dark_mode:
        # A separate override block rather than changing the base CSS above, so the
        # default light theme (and all the contrast/readability fixes already tuned
        # for it) stays completely untouched when the toggle is off. Risk colors
        # (green/amber/red) are left alone since they're semantic, not theme-driven.
        st.markdown(
            """
            <style>
            .stApp { background-color: #0F172A !important; }
            [data-testid="stAppViewContainer"] { background-color: #0F172A !important; }
            [data-testid="stHeader"] { background-color: transparent !important; }
            .stApp, .stApp p, .stApp label,
            h1:not([style]), h2:not([style]), h3:not([style]), h4:not([style]),
            h5:not([style]), h6:not([style]) { color: #E2E8F0 !important; }
            /* Deliberately NOT overriding span color globally, and excluding any
               heading with its own inline style (e.g. the "Moderate Risk" h3, which
               sets its own semantic risk color) - those set their own color for a
               reason, and a blanket override here makes them unreadable or wrong
               (e.g. light text on the tooltip "i" icon's light background, or the
               risk-level heading losing its red/amber/green meaning). */
            .risk-card, .kpi-card, .note-card, .rec-card {
                background: #1E293B !important;
                box-shadow: 0 1px 3px rgba(0,0,0,0.4) !important;
            }
            .risk-card .risk-label, .kpi-card .kpi-label { color: #94A3B8 !important; }
            .kpi-card .kpi-caption { color: #64748B !important; }
            [data-baseweb="tab-list"] { background-color: #1E293B !important; }
            .stTabs [data-baseweb="tab"] { color: #94A3B8 !important; }
            .stTabs [aria-selected="true"] { color: #E2E8F0 !important; }
            [data-testid="stMetricValue"], [data-testid="stMetricLabel"] { color: #E2E8F0 !important; }
            </style>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("---")

    with st.container(border=True):
        st.markdown("**Risk Time Horizon**")

        company_name = st.selectbox(
            "Company Name",
            options=KNOWN_COMPANIES,
            index=None,
            placeholder="e.g., Apple, Toyota, Pfizer",
            help="Pick a suggestion or type any company - its industry is detected automatically",
            accept_new_options=True,
        )
        company_name = company_name or ""

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

        industry = st.selectbox("Select Industry *", options=INDUSTRIES, index=0, key="industry_select")

        time_horizon = st.segmented_control(
            "Time Range *",
            options=["30 days", "90 days", "180 days"],
            format_func=lambda v: v.replace(" days", "d"),
            default="90 days",
            required=True,
        )

    st.markdown("---")
    st.caption("Data sources: FRED, Alpha Vantage, World Bank, NewsAPI")

# ---- HEADER ----
st.title("Supply Chain Risk Monitor")

badges = ""
if company_name:
    if company_name in COMPANY_LOGO_DOMAINS:
        logo_url = f"https://www.google.com/s2/favicons?domain={COMPANY_LOGO_DOMAINS[company_name]}&sz=64"
        company_icon = (
            f'<img src="{logo_url}" alt="" '
            f'style="width:18px; height:18px; object-fit:contain; border-radius:4px; '
            f'background:#fff; padding:2px;" '
            f"onerror=\"this.style.display='none'; this.nextElementSibling.style.display='inline';\">"
            f'<span style="display:none;">🏢</span>'
        )
    else:
        company_icon = "🏢"
    badges += (
        '<span style="background:#0F172A; color:#FFFFFF; padding:5px 14px; '
        'border-radius:20px; font-size:13px; font-weight:700; display:inline-flex; '
        'align-items:center; gap:7px;">'
        f"{company_icon} {company_name}</span>"
    )
if company_name and not detected_industry:
    badges += (
        '<span style="background:#FEF3C7; color:#92400E; padding:5px 14px; '
        'border-radius:20px; font-size:13px; font-weight:700;">'
        f"Industry not recognized for '{company_name}' - showing dropdown selection</span>"
    )

if badges:
    st.markdown(
        f"""<div style="display:flex; flex-wrap:wrap; gap:8px; margin-top:-10px; margin-bottom:20px;">{badges}</div>""",
        unsafe_allow_html=True,
    )

# ---- RISK SCORE SECTION ----
with st.spinner("Fetching live data and calculating risk scores..."):
    base_result = get_cached_risk_score(industry)

# Company name only nudges scores when the AI has real, specific knowledge of that
# company - otherwise it stays at the pure industry baseline. This keeps the dashboard
# honest: a made-up or obscure name can't silently inflate/deflate the displayed risk.
industry_weights = get_weights(industry)
adjusted_sub_scores = dict(base_result["sub_scores"])
company_adjustment = None
if company_name:
    with st.spinner(f"Checking company-specific factors for {company_name}..."):
        company_adjustment = get_cached_company_adjustment(company_name, industry)
    if company_adjustment["known"]:
        for key in industry_weights:
            adjusted_sub_scores[key] = round(
                max(0, min(100, adjusted_sub_scores[key] + company_adjustment[key])), 1
            )

adjusted_total = round(sum(adjusted_sub_scores[key] * industry_weights[key] for key in industry_weights), 1)
result = {
    "industry": industry,
    "total": adjusted_total,
    "label": get_risk_label(adjusted_total),
    "sub_scores": adjusted_sub_scores,
    "weights": industry_weights,
    "details": base_result["details"],
}

# Computed early (rather than inside the Summary tab where it's also displayed) so
# a real-time banner can surface critical alerts right at the top of the page,
# before the user even picks a tab.
critical_alerts = sorted(
    [(RISK_CATEGORY_LABELS[key], score) for key, score in result["sub_scores"].items() if score > 60],
    key=lambda x: -x[1],
)
if critical_alerts:
    alert_text = " &nbsp;|&nbsp; ".join(f"{label}: {score}" for label, score in critical_alerts)
    st.markdown(
        f"""<div style="background:#FEE2E2; border:1px solid #FCA5A5; border-radius:10px;
        padding:12px 18px; margin-bottom:16px; display:flex; align-items:center; gap:10px; flex-wrap:wrap;">
        <span style="font-size:20px;">⚠️</span>
        <span style="color:#991B1B; font-weight:700;">Critical Risk Alert:</span>
        <span style="color:#991B1B;">{alert_text}</span>
        </div>""",
        unsafe_allow_html=True,
    )

overall_tooltip = info_icon(
    "Weighted average of 5 categories for "
    f"{industry}: Supplier Concentration ({industry_weights['supplier']:.0%}), "
    f"Commodity Price ({industry_weights['commodity']:.0%}), "
    f"Logistics & Shipping ({industry_weights['logistics']:.0%}), "
    f"Geopolitical ({industry_weights['geopolitical']:.0%}), "
    f"and Regulatory & Trade ({industry_weights['regulatory']:.0%}). "
    "Each category score itself combines Probability, Impact, and Current State "
    "where independent real data supports it."
)
st.markdown(f"## Overall Risk Assessment{overall_tooltip}", unsafe_allow_html=True)

with st.container(width=360, key="gauge_container"):
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
        width=360,
        height=280,
        margin=dict(t=50, b=10, l=30, r=40),
        font=dict(family="Inter, sans-serif", color="#1E293B"),
    )
    # Wrapped in a fixed-width (360px) container above, not a flexible column -
    # letting a shrinking column stretch/squish this gauge while height stays fixed
    # distorts the semi-circle shape and makes the number overlap the arc. A fixed
    # container renders identically everywhere instead of degrading unpredictably.
    st.plotly_chart(fig, width="stretch")

    color = get_risk_color(result["total"])
    st.markdown(
        f"<h3 style='text-align:center; color:{color}'>{result['label']}</h3>",
        unsafe_allow_html=True,
    )

SUB_SCORE_CARDS = [
    (
        "supplier", "Supplier Concentration", "🏭",
        "How dependent this industry is on a small number of suppliers/countries. "
        "A hand-researched baseline, since this shifts over years, not days.",
    ),
    (
        "commodity", "Commodity Price", "📦",
        "Live price trend + volatility across this industry's tracked raw materials "
        "(FRED + Alpha Vantage), looking at the last 90 days.",
    ),
    (
        "logistics", "Logistics & Shipping", "🚢",
        "Status of 5 major shipping routes (Red Sea, Panama Canal, US ports, Strait "
        "of Malacca), plus a live news-spike layer for sudden disruptions.",
    ),
    (
        "geopolitical", "Geopolitical", "🌍",
        "World Bank political-stability data for this industry's sourcing countries, "
        "weighted by sourcing share, plus a live news-spike layer.",
    ),
    (
        "regulatory", "Regulatory & Trade", "📜",
        "Tariffs, export controls, and trade-policy exposure for this industry, "
        "plus a live news-spike layer for breaking tariff/trade headlines.",
    ),
]

st.markdown("<br>", unsafe_allow_html=True)
cards_html = "".join(
    score_card_html(label, result["sub_scores"][key], icon, description)
    for key, label, icon, description in SUB_SCORE_CARDS
)
st.markdown(
    f'<div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 6px;">{cards_html}</div>',
    unsafe_allow_html=True,
)

with st.expander("Drill down into a category"):
    drill_tabs = st.tabs([label for _, label, _, _ in SUB_SCORE_CARDS])

    with drill_tabs[0]:  # Supplier
        st.caption(
            "No further breakdown available - this is a single hand-curated industry baseline, "
            "not assembled from multiple sub-signals like the other categories."
        )

    with drill_tabs[1]:  # Commodity
        for name, data in result["details"]["commodity"]["by_commodity"].items():
            st.markdown(f"**{name}**")
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Probability", data["probability"])
            c2.metric("Impact", data["impact"])
            c3.metric("Current State", data["current_state"])
            c4.metric("Combined", data["combined"])

    with drill_tabs[2]:  # Logistics
        for name, data in result["details"]["logistics"]["by_route"].items():
            st.markdown(f"**{name}**")
            c1, c2, c3 = st.columns(3)
            c1.metric("Base", data["base"])
            c2.metric("News Alert", f"+{data['alert_adjustment']}")
            c3.metric("Final", data["final"])

    with drill_tabs[3]:  # Geopolitical
        for code, data in result["details"]["geopolitical"]["by_country"].items():
            st.markdown(f"**{data['name']}** ({code}) - sourcing weight {data['weight']:.0%}")
            c1, c2, c3 = st.columns(3)
            c1.metric("Base", data["base"])
            c2.metric("News Alert", f"+{data['alert_adjustment']}")
            c3.metric("Final", data["final"])

    with drill_tabs[4]:  # Regulatory
        reg = result["details"]["regulatory"]
        c1, c2 = st.columns(2)
        c1.metric("Baseline", reg["base"])
        c2.metric("News Alert", f"+{reg['alert_adjustment']}")
        st.caption(reg["summary"])

# ---- DETAIL TABS (placeholders for now) ----
st.markdown("---")
st.markdown("## Detailed Analysis")

tab1, tab2, tab3, tab4 = st.tabs(
    ["📈 Commodity Prices", "🚢 Shipping Routes", "🌍 Geopolitical Map", "📋 Summary & Recommendations"]
)

with tab1:
    st.markdown("### Commodity Price Trends")

    commodity_data = get_cached_commodity_prices(industry)
    unavailable_commodities = []

    for commodity_name, history in commodity_data.items():
        if len(history) < 2:
            unavailable_commodities.append(commodity_name)
            continue

        fig = build_commodity_chart(commodity_name, history)
        st.plotly_chart(fig, use_container_width=True)

    if unavailable_commodities:
        st.caption(f"Updating: {', '.join(unavailable_commodities)} will appear shortly.")

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

    fig = build_geo_choropleth(by_country)
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
    # Still computed (not displayed directly anymore) since Supplier Risk's
    # compliance check below depends on it.
    known_suppliers = []
    if company_name and detected_industry:
        with st.spinner(f"Looking up {company_name}'s suppliers..."):
            known_suppliers = get_cached_known_suppliers(company_name, industry)

    st.markdown("### Supplier Risk")

    supplier_score = result["sub_scores"]["supplier"]

    if by_country:
        top_code, top_data = max(by_country.items(), key=lambda x: x[1]["weight"])
        top_pct = top_data["weight"] * 100
        if top_pct >= 50:
            dep_label, dep_color = "High", "#E74C3C"
        elif top_pct >= 30:
            dep_label, dep_color = "Moderate", "#F39C12"
        else:
            dep_label, dep_color = "Low", "#2ECC71"
        dependency_value = f"{dep_label}"
        dependency_caption = f"{top_pct:.0f}% sourced from {top_data['name']}"
    else:
        dep_label, dep_color, top_data, top_pct = "Unknown", "#94A3B8", None, 0
        dependency_value = "Unknown"
        dependency_caption = "No sourcing data available."

    compliance_targets = (
        [s["supplier"] for s in known_suppliers] if known_suppliers
        else ([company_name] if company_name else [])
    )
    compliance_results = []
    if compliance_targets:
        with st.spinner("Checking US Consolidated Screening List..."):
            compliance_results = [(name, get_cached_sanctions_status(name)) for name in compliance_targets]

    flagged = [(name, r) for name, r in compliance_results if r["sanctioned"]]
    any_checked = any(r["checked"] for _, r in compliance_results)

    if flagged:
        compliance_value, compliance_color = "Flagged", "#E74C3C"
        compliance_caption = "; ".join(f"{name}: {r['matched_name']} (verify manually)" for name, r in flagged)
    elif any_checked:
        compliance_value, compliance_color = "Clear", "#2ECC71"
        compliance_caption = "No name match found on the US Consolidated Screening List."
    elif not compliance_targets:
        compliance_value, compliance_color = "N/A", "#94A3B8"
        compliance_caption = "No company or named supplier to check."
    else:
        compliance_value, compliance_color = "Not Checked", "#94A3B8"
        compliance_caption = "Compliance screening API key not configured."

    st.markdown(
        '<div style="display:grid; grid-template-columns:repeat(auto-fit, minmax(220px, 1fr)); gap:12px;">'
        + kpi_card_html(
            "Supplier Risk Rating",
            f"{supplier_score} <span style='font-size:15px;'>({get_risk_label(supplier_score)})</span>",
            None, get_risk_color(supplier_score),
        )
        + kpi_card_html("Single Source Dependency", dependency_value, dependency_caption, dep_color)
        + kpi_card_html("Supplier Compliance Status", compliance_value, compliance_caption, compliance_color)
        + '</div>',
        unsafe_allow_html=True,
    )

    st.markdown("---")
    st.markdown("### Logistics Risk")

    port_routes = [name for name in SHIPPING_STATUS if "Port" in name]
    avg_delay_days = sum(
        SHIPPING_STATUS[route]["delay_days"] * weight for route, weight in ROUTE_WEIGHTS.items()
    )
    port_congestion_score = (
        sum(logistics_result["by_route"][route]["final"] for route in port_routes) / len(port_routes)
        if port_routes else 0
    )
    transportation_risk_index = logistics_result["score"]
    on_time_rate = get_on_time_delivery_estimate(transportation_risk_index)

    if avg_delay_days <= 2:
        delay_label, delay_color = "Low", "#2ECC71"
    elif avg_delay_days <= 5:
        delay_label, delay_color = "Moderate", "#F39C12"
    elif avg_delay_days <= 10:
        delay_label, delay_color = "High", "#E67E22"
    else:
        delay_label, delay_color = "Critical", "#E74C3C"

    st.markdown(
        '<div style="display:grid; grid-template-columns:repeat(auto-fit, minmax(220px, 1fr)); gap:12px;">'
        + kpi_card_html(
            "Shipment Delays",
            f"{avg_delay_days:.1f} days <span style='font-size:15px;'>({delay_label})</span>",
            "Weighted average delay across tracked routes, by share of global trade volume.",
            delay_color,
        )
        + kpi_card_html(
            "Port Congestion",
            f"{port_congestion_score:.1f} <span style='font-size:15px;'>({get_risk_label(port_congestion_score)})</span>"
            if port_routes else "N/A",
            f"Average risk score across {', '.join(port_routes)}." if port_routes else "No tracked port routes available.",
            get_risk_color(port_congestion_score) if port_routes else "#94A3B8",
        )
        + kpi_card_html(
            "Transportation Risk Index",
            f"{transportation_risk_index} <span style='font-size:15px;'>({get_risk_label(transportation_risk_index)})</span>",
            "Same overall score as the Logistics & Shipping risk category.",
            get_risk_color(transportation_risk_index),
        )
        + kpi_card_html(
            "On-Time Delivery Rate",
            f"{on_time_rate:.1f}%",
            "Estimate derived from the Transportation Risk Index, not a carrier-reported statistic.",
            get_risk_color(100 - on_time_rate),
        )
        + '</div>',
        unsafe_allow_html=True,
    )

    st.markdown("---")
    st.markdown("### Geographic & External Risk")

    top_country_name = top_data["name"] if top_data else None
    pol_reg_score = round((result["sub_scores"]["geopolitical"] + result["sub_scores"]["regulatory"]) / 2, 1)

    if top_country_name:
        with st.spinner(f"Checking disaster-related news for {top_country_name}..."):
            disaster_alert = get_cached_disaster_alert(top_country_name)
        disaster_label, disaster_color = get_alert_band(disaster_alert["adjustment"])
        disaster_caption = (
            f"{top_country_name} (top sourcing country): {disaster_alert['recent_count']} recent mentions "
            f"vs {disaster_alert['baseline_weekly_rate']}/week normal."
        )
    else:
        disaster_alert = _EMPTY_ALERT
        disaster_label, disaster_color = "N/A", "#94A3B8"
        disaster_caption = "No sourcing data available to check."

    if top_country_name:
        with st.spinner(f"Checking weather-related news for {top_country_name}..."):
            weather_alert = get_cached_weather_alert(top_country_name)
        weather_label, weather_color = get_alert_band(weather_alert["adjustment"])
        weather_caption = (
            f"{top_country_name} (top sourcing country): {weather_alert['recent_count']} recent mentions "
            f"vs {weather_alert['baseline_weekly_rate']}/week normal."
        )
    else:
        weather_alert = _EMPTY_ALERT
        weather_label, weather_color = "N/A", "#94A3B8"
        weather_caption = "No sourcing data available to check."

    if top_country_name:
        with st.spinner(f"Checking conflict-related news for {top_country_name}..."):
            conflict_alert = get_cached_conflict_alert(top_country_name)
        conflict_label, conflict_color = get_alert_band(conflict_alert["adjustment"])
        conflict_caption = (
            f"{top_country_name} (top sourcing country): {conflict_alert['recent_count']} recent mentions "
            f"vs {conflict_alert['baseline_weekly_rate']}/week normal."
        )
    else:
        conflict_alert = _EMPTY_ALERT
        conflict_label, conflict_color = "N/A", "#94A3B8"
        conflict_caption = "No sourcing data available to check."

    st.markdown(
        '<div style="display:grid; grid-template-columns:repeat(auto-fit, minmax(220px, 1fr)); gap:12px;">'
        + kpi_card_html("Natural Disaster Alerts", disaster_label, disaster_caption, disaster_color)
        + kpi_card_html(
            "Political/Regulatory Risks",
            f"{pol_reg_score} <span style='font-size:15px;'>({get_risk_label(pol_reg_score)})</span>",
            "Average of the Geopolitical and Regulatory & Trade risk scores.",
            get_risk_color(pol_reg_score),
        )
        + kpi_card_html("Weather Impact", weather_label, weather_caption, weather_color)
        + kpi_card_html("Regional Conflict Alerts", conflict_label, conflict_caption, conflict_color)
        + '</div>',
        unsafe_allow_html=True,
    )

    st.markdown("---")
    st.markdown("### Dashboard Visualization")

    st.markdown("**Risk Ranking**")
    with st.spinner("Computing risk scores across all industries..."):
        all_industry_scores = {ind: get_cached_risk_score(ind)["sub_scores"] for ind in INDUSTRIES}
        all_industry_weights = {ind: get_weights(ind) for ind in INDUSTRIES}
    st.plotly_chart(build_risk_ranking_chart(all_industry_scores, all_industry_weights), use_container_width=True)
    st.caption("All 11 industries ranked by overall risk score, broken down by each category's actual contribution.")

    st.markdown("**Trend Analysis**")
    record_score_snapshot(industry, result["total"], result["sub_scores"])
    score_history = get_score_history(industry)
    st.plotly_chart(build_score_trend_chart(score_history), use_container_width=True)
    if len(score_history) <= 1:
        st.caption(f"Tracking starts today - check back over time to see {industry}'s risk score trend build up.")
    else:
        st.caption(f"{industry}'s overall risk score over the last {len(score_history)} recorded day(s).")

    st.markdown("---")

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

    st.markdown("### Export Report")
    col_pdf, col_xlsx = st.columns(2)
    with col_pdf:
        st.download_button(
            "Download PDF",
            data=get_cached_pdf_report(
                industry, company_name, time_horizon, result, ai_summary, recommendations,
                commodity_data, SHIPPING_STATUS, logistics_result, by_country,
                (dep_label, top_pct, top_data["name"] if top_data else None), compliance_results,
                (avg_delay_days, delay_label), (port_congestion_score, port_routes), on_time_rate,
                top_country_name, disaster_alert, pol_reg_score, weather_alert, conflict_alert,
                all_industry_scores, all_industry_weights, score_history,
            ),
            file_name=f"supply_chain_risk_{industry.lower().replace(' ', '_')}.pdf",
            mime="application/pdf",
            width="stretch",
        )
    with col_xlsx:
        st.download_button(
            "Download Excel",
            data=get_cached_excel_report(
                industry, company_name, time_horizon, result, ai_summary, recommendations,
                commodity_data, SHIPPING_STATUS, logistics_result, by_country,
                (dep_label, top_pct, top_data["name"] if top_data else None), compliance_results,
                (avg_delay_days, delay_label), (port_congestion_score, port_routes), on_time_rate,
                top_country_name, disaster_alert, pol_reg_score, weather_alert, conflict_alert,
                all_industry_scores, all_industry_weights, score_history,
            ),
            file_name=f"supply_chain_risk_{industry.lower().replace(' ', '_')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            width="stretch",
        )
