import streamlit as st

# Thin entry point - Streamlit Cloud's "Main file path" setting is pinned to this
# filename, so it must never be renamed (a prior attempt at renaming this file broke
# the live deployment, since that setting isn't editable after the app is created on
# newer Streamlit Cloud). The actual page content lives in risk_monitor_view.py and
# pages/*.py, referenced below by file path - this is what lets st.navigation show a
# custom "Risk Monitor" sidebar label instead of the filename-derived one, without
# touching this file's name.
#
# st.set_page_config() must be called exactly once, here, before st.navigation() -
# none of the referenced page files call it themselves.
st.set_page_config(
    page_title="Risk Monitor - SupplyIQ",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="auto",
)

pg = st.navigation([
    st.Page("risk_monitor_view.py", title="Risk Monitor", icon="🔍", default=True),
    st.Page("pages/1_Supply_Chain_Simulator.py", title="Supply Chain Simulator", icon="🧭"),
    st.Page("pages/2_Demand_Forecasting.py", title="Demand Forecasting", icon="📈"),
    st.Page("pages/3_Supplier_Scorecard.py", title="Supplier Scorecard", icon="📋"),
    st.Page("pages/4_Logistics_Route_Optimizer.py", title="Logistics Route Optimizer", icon="🚚"),
    st.Page("pages/5_Cost_Optimization.py", title="Cost Optimization", icon="💰"),
    st.Page("pages/6_Executive_Dashboard.py", title="Executive Dashboard", icon="🏠"),
])
pg.run()
