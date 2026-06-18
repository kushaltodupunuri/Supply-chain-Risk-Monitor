import streamlit as st

from src.ui_helpers import inject_shared_css, cards_grid, metric_card_html

st.set_page_config(page_title="Cost Optimization - SupplyIQ", page_icon="💰", layout="wide")
inject_shared_css()

st.title("💰 Cost Optimization Engine")
st.caption("Find the Hidden Money in Your Supply Chain")

st.markdown(
    "This pulls in data you've already entered on the Supplier Scorecard and Logistics "
    "pages where available, and asks for a few more numbers to estimate savings in the "
    "areas those pages don't cover. Every number below is an estimate built from "
    "adjustable assumptions, not a measured figure - the point is to point you at where "
    "to look, not to be exact to the dollar."
)

supplier_df = st.session_state.get("supplier_df")
dest_df = st.session_state.get("dest_df")

savings_breakdown = []

st.markdown("---")
st.markdown("### 1. Supplier Consolidation")
if supplier_df is not None and len(supplier_df.dropna(subset=["Supplier"])) >= 2:
    sdf = supplier_df.dropna(subset=["Supplier"])
    st.caption(f"Using your {len(sdf)} suppliers from the Supplier Scorecard page.")
    unit_cost = st.number_input("Average unit cost across these suppliers ($)", min_value=0.0, value=12.0, step=0.5)
    monthly_spend = (sdf["Monthly Orders"] * unit_cost).sum()
    price_spread = sdf["Price Variance %"].max() - sdf["Price Variance %"].min()
    consolidation_savings = monthly_spend * (price_spread / 100) * 0.5
    st.write(
        f"You're buying from {len(sdf)} suppliers with a {price_spread:.0f}-point spread in price "
        f"consistency. Consolidating more volume toward your most price-stable supplier could "
        f"capture roughly half that spread."
    )
else:
    st.caption("No supplier data found yet - visit the Supplier Scorecard page, or enter rough numbers here.")
    col1, col2, col3 = st.columns(3)
    with col1:
        num_suppliers = st.number_input("Suppliers for the same material/product", min_value=1, value=3)
    with col2:
        monthly_spend = st.number_input("Combined monthly spend across them ($)", min_value=0, value=4000, step=100)
    with col3:
        price_spread = st.number_input("Price spread between cheapest and priciest (%)", min_value=0, value=12, step=1)
    consolidation_savings = monthly_spend * (price_spread / 100) * 0.5

savings_breakdown.append(("Supplier Consolidation", consolidation_savings,
                           f"You're paying inconsistent prices across suppliers for similar goods - "
                           f"consolidating more volume with your best-priced, most reliable supplier "
                           f"saves an estimated ${consolidation_savings:,.0f}/month."))

st.markdown("---")
st.markdown("### 2. Inventory Carrying Cost")
col1, col2 = st.columns(2)
with col1:
    excess_inventory_value = st.number_input("Value of slow-moving / excess inventory ($)", min_value=0, value=8000, step=500)
with col2:
    carrying_rate_pct = st.number_input("Annual carrying cost rate (%) - storage, capital, obsolescence, insurance", min_value=0, value=25, step=1)
carrying_cost_monthly = excess_inventory_value * (carrying_rate_pct / 100) / 12
savings_breakdown.append(("Inventory Carrying Cost", carrying_cost_monthly,
                           f"You're holding ${excess_inventory_value:,.0f} in slow-moving inventory - "
                           f"at a typical {carrying_rate_pct:.0f}%/year carrying cost, that's about "
                           f"${carrying_cost_monthly:,.0f}/month just to keep it sitting there. "
                           f"Liquidating it (discount, bundle, write off) frees that money up."))

st.markdown("---")
st.markdown("### 3. Shipping Cost Leakage")
if dest_df is not None and len(dest_df.dropna(subset=["City"])) >= 1:
    total_orders = dest_df["Monthly Orders"].sum()
    st.caption(f"Using {total_orders:.0f} monthly orders from the Logistics page.")
else:
    total_orders = st.number_input("Total monthly orders shipped", min_value=0, value=200, step=10)
col1, col2 = st.columns(2)
with col1:
    pct_unnecessary_express = st.slider("% of orders sent Express/Overnight that didn't need to be", 0, 100, 34)
with col2:
    express_premium = st.number_input("Average extra cost of Express vs. Standard, per order ($)", min_value=0.0, value=4.5, step=0.5)
shipping_leakage = total_orders * (pct_unnecessary_express / 100) * express_premium
savings_breakdown.append(("Shipping Cost Leakage", shipping_leakage,
                           f"You're using expedited shipping for {pct_unnecessary_express}% of orders that "
                           f"probably don't need it. Switching those to standard shipping saves an "
                           f"estimated ${shipping_leakage:,.0f}/month."))

st.markdown("---")
st.markdown("### 4. Demand-Supply Mismatch (Stockouts)")
col1, col2 = st.columns(2)
with col1:
    lost_units = st.number_input("Estimated units of lost sales last quarter due to stockouts", min_value=0, value=80, step=5)
with col2:
    revenue_per_unit = st.number_input("Average revenue per unit ($)", min_value=0.0, value=40.0, step=5.0)
stockout_cost_monthly = (lost_units * revenue_per_unit) / 3
savings_breakdown.append(("Demand-Supply Mismatch", stockout_cost_monthly,
                           f"Stockouts last quarter cost an estimated ${lost_units * revenue_per_unit:,.0f} "
                           f"in lost sales (~${stockout_cost_monthly:,.0f}/month) - better demand forecasting "
                           f"and reorder timing (see the Demand Forecasting page) directly addresses this."))

st.markdown("---")
total_savings = sum(s for _, s, _ in savings_breakdown)
st.session_state["cost_optimization_result"] = {
    "total_savings": total_savings, "savings_breakdown": savings_breakdown,
}
st.markdown(
    cards_grid([
        metric_card_html("Total Monthly Savings Identified", f"${total_savings:,.0f}",
                          f"~${total_savings * 12:,.0f}/year across 4 categories", "#2ECC71"),
    ] + [
        metric_card_html(name, f"${value:,.0f}/mo", None, "#4F46E5")
        for name, value, _ in savings_breakdown
    ]),
    unsafe_allow_html=True,
)

st.markdown("### What To Do About It")
for name, value, explanation in sorted(savings_breakdown, key=lambda x: -x[1]):
    st.markdown(f'<div class="action-item">💡 <b>{name}</b> — {explanation}</div>', unsafe_allow_html=True)
